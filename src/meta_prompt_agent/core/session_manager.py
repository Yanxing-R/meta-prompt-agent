# src/meta_prompt_agent/core/session_manager.py
import os
import json
import time
import uuid
import logging
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

from meta_prompt_agent.config import settings

logger = logging.getLogger(__name__)

# 会话阶段枚举
class SessionStage(str, Enum):
    """会话处理的各个阶段"""
    CREATED = "created"                      # 会话刚创建
    P1_GENERATED = "p1_generated"            # 已生成初步P1提示词
    EVALUATION_COMPLETE = "evaluation_complete"  # 评估完成
    REFINEMENT_COMPLETE = "refinement_complete"  # 优化/精炼完成
    COMPLETED = "completed"                  # 会话已完成

# 最大历史消息长度
MAX_HISTORY_LENGTH = 20

class PromptSession:
    """交互式提示词生成会话
    
    存储分步交互式提示词生成过程中的所有状态和中间结果
    """
    def __init__(
        self, 
        session_id: str, 
        user_raw_request: str, 
        task_type: str,
        model_override: Optional[str] = None, 
        provider_override: Optional[str] = None,
        template_name: Optional[str] = None,
        template_variables: Optional[Dict[str, Any]] = None
    ):
        """初始化会话对象
        
        Args:
            session_id: 会话的唯一标识符
            user_raw_request: 用户的原始请求文本
            task_type: 任务类型 (如 "通用/问答", "代码生成" 等)
            model_override: 可选的模型覆盖
            provider_override: 可选的提供商覆盖
            template_name: 可选的结构化模板名称
            template_variables: 可选的模板变量
        """
        self.session_id = session_id
        self.user_raw_request = user_raw_request
        self.task_type = task_type
        self.stage = SessionStage.CREATED
        self.created_at = datetime.now().isoformat()
        self.last_updated = self.created_at
        
        # 处理结果
        self.p1_prompt = ""  # 初始优化提示词
        self.initial_core_prompt = ""  # 初始核心提示模板
        self.evaluation_reports = []  # 所有评估报告
        self.refined_prompts = []  # 所有优化后的提示词
        self.current_prompt = ""  # 当前活跃的提示词
        self.current_evaluation = None  # 最近的评估报告
        self.final_prompt = ""  # 最终确定的提示词
        
        # 配置信息
        self.model_override = model_override
        self.provider_override = provider_override
        self.template_name = template_name
        self.template_variables = template_variables
        
        # 会话历史和错误处理
        self.conversation_history = []  # 与LLM的对话历史
        self.last_error = None  # 最近的错误信息
        self.error_stage = None  # 发生错误的阶段
        self.retries = {  # 各阶段的重试次数
            "p1_generation": 0,
            "evaluation": 0,
            "refinement": 0
        }
        
        # 用户交互记录
        self.user_modifications = []  # 用户的修改记录
        self.feedback = None  # 用户最终反馈
        
        # 递归优化设置
        self.current_recursion_depth = 0
        self.max_recursion_depth = 3  # 默认最大递归深度为3
        
        logger.info(f"创建了新会话 {session_id}，任务类型: {task_type}")
    
    def to_dict(self) -> Dict[str, Any]:
        """将会话转换为字典，用于序列化"""
        return {
            "session_id": self.session_id,
            "user_raw_request": self.user_raw_request,
            "task_type": self.task_type,
            "stage": self.stage,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "p1_prompt": self.p1_prompt,
            "initial_core_prompt": self.initial_core_prompt,
            "evaluation_reports": self.evaluation_reports,
            "refined_prompts": self.refined_prompts,
            "current_prompt": self.current_prompt,
            "final_prompt": self.final_prompt,
            "model_override": self.model_override,
            "provider_override": self.provider_override,
            "template_name": self.template_name,
            "template_variables": self.template_variables,
            "conversation_history": self.conversation_history,
            "last_error": self.last_error,
            "error_stage": self.error_stage,
            "retries": self.retries,
            "user_modifications": self.user_modifications,
            "feedback": self.feedback,
            "current_recursion_depth": self.current_recursion_depth,
            "max_recursion_depth": self.max_recursion_depth
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptSession':
        """从字典创建会话对象，用于反序列化"""
        session = cls(
            session_id=data["session_id"],
            user_raw_request=data["user_raw_request"],
            task_type=data["task_type"],
            model_override=data.get("model_override"),
            provider_override=data.get("provider_override"),
            template_name=data.get("template_name"),
            template_variables=data.get("template_variables")
        )
        
        # 恢复所有状态
        session.stage = data["stage"]
        session.created_at = data["created_at"]
        session.last_updated = data["last_updated"]
        session.p1_prompt = data["p1_prompt"]
        session.initial_core_prompt = data["initial_core_prompt"]
        session.evaluation_reports = data["evaluation_reports"]
        session.refined_prompts = data["refined_prompts"]
        session.current_prompt = data["current_prompt"]
        session.final_prompt = data["final_prompt"]
        session.conversation_history = data["conversation_history"]
        session.last_error = data["last_error"]
        session.error_stage = data["error_stage"]
        session.retries = data["retries"]
        session.user_modifications = data["user_modifications"]
        session.feedback = data["feedback"]
        session.current_recursion_depth = data["current_recursion_depth"]
        session.max_recursion_depth = data["max_recursion_depth"]
        
        return session
    
    def update_timestamp(self):
        """更新最后修改时间戳"""
        self.last_updated = datetime.now().isoformat()
    
    def add_to_history(self, role: str, content: str):
        """添加消息到对话历史
        
        Args:
            role: 消息角色 ("user", "assistant", "system")
            content: 消息内容
        """
        self.conversation_history.append({"role": role, "content": content})
        # 如果历史记录过长，保留最近的消息
        if len(self.conversation_history) > MAX_HISTORY_LENGTH:
            self.conversation_history = self.conversation_history[-MAX_HISTORY_LENGTH:]
        self.update_timestamp()
    
    def record_error(self, error_message: str, stage: Optional[str] = None):
        """记录错误信息
        
        Args:
            error_message: 错误描述
            stage: 发生错误的阶段，默认为当前阶段
        """
        self.last_error = error_message
        self.error_stage = stage or self.stage
        logger.error(f"会话 {self.session_id} 在阶段 {self.error_stage} 发生错误: {error_message}")
        self.update_timestamp()
    
    def record_user_modification(self, stage: str, original_prompt: str, modified_prompt: str, comments: Optional[str] = None):
        """记录用户对提示词的修改
        
        Args:
            stage: 修改的阶段 ("p1", "evaluation", "refinement")
            original_prompt: 原始提示词
            modified_prompt: 修改后的提示词
            comments: 用户对修改的说明
        """
        modification = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "original_prompt": original_prompt,
            "modified_prompt": modified_prompt,
            "comments": comments
        }
        self.user_modifications.append(modification)
        
        # 同时记录到对话历史
        user_message = f"用户修改了{stage}阶段的提示词"
        if comments:
            user_message += f"，说明：{comments}"
        self.add_to_history("system", user_message)
        
        self.update_timestamp()
    
    def increment_retry(self, stage_key: str) -> int:
        """增加特定阶段的重试计数
        
        Args:
            stage_key: 阶段键名 ("p1_generation", "evaluation", "refinement")
            
        Returns:
            当前重试次数
        """
        if stage_key in self.retries:
            self.retries[stage_key] += 1
            self.update_timestamp()
            return self.retries[stage_key]
        return 0
    
    def can_retry(self, stage_key: str, max_retries: int = 3) -> bool:
        """检查是否可以重试特定阶段
        
        Args:
            stage_key: 阶段键名
            max_retries: 最大重试次数
            
        Returns:
            是否可以重试
        """
        current_retries = self.retries.get(stage_key, 0)
        return current_retries < max_retries
    
    def get_summary(self) -> Dict[str, Any]:
        """获取会话摘要信息，用于UI展示"""
        return {
            "session_id": self.session_id,
            "user_request": self.user_raw_request[:100] + "..." if len(self.user_raw_request) > 100 else self.user_raw_request,
            "task_type": self.task_type,
            "stage": self.stage,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "has_p1": bool(self.p1_prompt),
            "evaluation_count": len(self.evaluation_reports),
            "refinement_count": len(self.refined_prompts),
            "has_final": bool(self.final_prompt),
            "has_error": bool(self.last_error),
            "model": self.model_override or "默认",
            "provider": self.provider_override or "默认",
            "template": self.template_name or "无"
        }


class SessionManager:
    """会话管理器
    
    负责会话的创建、存储、检索和清理
    """
    def __init__(self, storage_type: str = None):
        """初始化会话管理器
        
        Args:
            storage_type: 存储类型 ("memory", "redis", "file")，默认从配置中获取
        """
        self.storage_type = storage_type or getattr(settings, "SESSION_STORAGE_TYPE", "memory")
        self.sessions = {}  # 内存存储
        self.session_expiry = getattr(settings, "SESSION_EXPIRY_SECONDS", 3600)  # 默认1小时
        
        # 设置存储后端
        if self.storage_type == "redis":
            try:
                import redis
                redis_host = getattr(settings, "REDIS_HOST", "localhost")
                redis_port = getattr(settings, "REDIS_PORT", 6379)
                redis_db = getattr(settings, "REDIS_DB", 0)
                redis_password = getattr(settings, "REDIS_PASSWORD", None)
                
                self.redis_client = redis.Redis(
                    host=redis_host, 
                    port=redis_port, 
                    db=redis_db,
                    password=redis_password,
                    decode_responses=False  # 不自动解码，以便我们可以手动处理JSON
                )
                logger.info(f"使用Redis存储会话，连接到 {redis_host}:{redis_port}/{redis_db}")
            except ImportError:
                logger.warning("Redis包未安装，回退到内存存储")
                self.storage_type = "memory"
            except Exception as e:
                logger.error(f"连接Redis失败：{str(e)}，回退到内存存储")
                self.storage_type = "memory"
        
        elif self.storage_type == "file":
            # 创建会话存储目录
            self.session_dir = os.path.join(
                getattr(settings, "DATA_DIR", os.path.join(os.getcwd(), "data")), 
                "sessions"
            )
            os.makedirs(self.session_dir, exist_ok=True)
            logger.info(f"使用文件存储会话，目录：{self.session_dir}")
        
        logger.info(f"会话管理器初始化完成，存储类型：{self.storage_type}")
    
    def generate_session_id(self) -> str:
        """生成唯一的会话ID"""
        return f"sess_{uuid.uuid4().hex[:12]}_{int(time.time())}"
    
    async def create_session(
        self, 
        user_raw_request: str, 
        task_type: str,
        model_override: Optional[str] = None, 
        provider_override: Optional[str] = None,
        template_name: Optional[str] = None,
        template_variables: Optional[Dict[str, Any]] = None
    ) -> PromptSession:
        """创建新的会话
        
        Args:
            user_raw_request: 用户的原始请求
            task_type: 任务类型
            model_override: 可选的模型覆盖
            provider_override: 可选的提供商覆盖
            template_name: 可选的模板名称
            template_variables: 可选的模板变量
            
        Returns:
            新创建的会话对象
        """
        session_id = self.generate_session_id()
        session = PromptSession(
            session_id=session_id,
            user_raw_request=user_raw_request,
            task_type=task_type,
            model_override=model_override,
            provider_override=provider_override,
            template_name=template_name,
            template_variables=template_variables
        )
        
        # 保存会话
        await self.save_session(session)
        return session
    
    async def save_session(self, session: PromptSession) -> bool:
        """保存会话
        
        Args:
            session: 要保存的会话对象
            
        Returns:
            保存是否成功
        """
        try:
            session.update_timestamp()
            
            if self.storage_type == "memory":
                self.sessions[session.session_id] = session
            
            elif self.storage_type == "redis":
                serialized = json.dumps(session.to_dict(), ensure_ascii=False)
                self.redis_client.setex(
                    f"session:{session.session_id}", 
                    self.session_expiry, 
                    serialized.encode('utf-8')
                )
            
            elif self.storage_type == "file":
                file_path = os.path.join(self.session_dir, f"{session.session_id}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
            
            logger.debug(f"会话 {session.session_id} 保存成功，当前阶段：{session.stage}")
            return True
        
        except Exception as e:
            logger.error(f"保存会话 {session.session_id} 失败：{str(e)}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[PromptSession]:
        """获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话对象，如果不存在返回None
        """
        try:
            if self.storage_type == "memory":
                return self.sessions.get(session_id)
            
            elif self.storage_type == "redis":
                data = self.redis_client.get(f"session:{session_id}")
                if data:
                    # 从Redis获取的数据需要解码
                    session_dict = json.loads(data.decode('utf-8'))
                    return PromptSession.from_dict(session_dict)
            
            elif self.storage_type == "file":
                file_path = os.path.join(self.session_dir, f"{session_id}.json")
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        session_dict = json.load(f)
                        return PromptSession.from_dict(session_dict)
            
            logger.warning(f"会话 {session_id} 不存在")
            return None
        
        except Exception as e:
            logger.error(f"获取会话 {session_id} 失败：{str(e)}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            删除是否成功
        """
        try:
            if self.storage_type == "memory":
                if session_id in self.sessions:
                    del self.sessions[session_id]
                    return True
            
            elif self.storage_type == "redis":
                result = self.redis_client.delete(f"session:{session_id}")
                return result > 0
            
            elif self.storage_type == "file":
                file_path = os.path.join(self.session_dir, f"{session_id}.json")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"删除会话 {session_id} 失败：{str(e)}")
            return False
    
    async def list_sessions(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """列出会话摘要信息
        
        Args:
            limit: 返回的最大会话数量
            offset: 分页偏移量
            
        Returns:
            会话摘要列表
        """
        try:
            summaries = []
            
            if self.storage_type == "memory":
                # 对会话按创建时间排序
                sorted_sessions = sorted(
                    self.sessions.values(),
                    key=lambda s: s.created_at,
                    reverse=True
                )
                # 应用分页
                paged_sessions = sorted_sessions[offset:offset+limit]
                summaries = [session.get_summary() for session in paged_sessions]
            
            elif self.storage_type == "redis":
                # 获取所有会话键
                keys = self.redis_client.keys("session:*")
                # 应用分页
                paged_keys = keys[offset:offset+limit]
                for key in paged_keys:
                    data = self.redis_client.get(key)
                    if data:
                        session_dict = json.loads(data.decode('utf-8'))
                        session = PromptSession.from_dict(session_dict)
                        summaries.append(session.get_summary())
            
            elif self.storage_type == "file":
                # 获取目录中的所有会话文件
                files = [f for f in os.listdir(self.session_dir) if f.endswith('.json')]
                # 按文件修改时间排序
                files.sort(key=lambda f: os.path.getmtime(os.path.join(self.session_dir, f)), reverse=True)
                # 应用分页
                paged_files = files[offset:offset+limit]
                for file_name in paged_files:
                    file_path = os.path.join(self.session_dir, file_name)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        session_dict = json.load(f)
                        session = PromptSession.from_dict(session_dict)
                        summaries.append(session.get_summary())
            
            return summaries
        
        except Exception as e:
            logger.error(f"列出会话失败：{str(e)}")
            return []
    
    async def clean_expired_sessions(self) -> int:
        """清理过期会话
        
        Returns:
            清理的会话数量
        """
        try:
            cleaned_count = 0
            now = datetime.now()
            expiry_time = now - timedelta(seconds=self.session_expiry)
            
            if self.storage_type == "memory":
                # 查找过期会话
                expired_ids = [
                    sid for sid, session in self.sessions.items()
                    if datetime.fromisoformat(session.last_updated) < expiry_time
                ]
                # 删除过期会话
                for sid in expired_ids:
                    del self.sessions[sid]
                cleaned_count = len(expired_ids)
            
            elif self.storage_type == "file":
                # 遍历所有会话文件
                for file_name in os.listdir(self.session_dir):
                    if not file_name.endswith('.json'):
                        continue
                    
                    file_path = os.path.join(self.session_dir, file_name)
                    # 检查文件修改时间
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if mod_time < expiry_time:
                        os.remove(file_path)
                        cleaned_count += 1
            
            # Redis会自动过期，不需要手动清理
            
            if cleaned_count > 0:
                logger.info(f"清理了 {cleaned_count} 个过期会话")
            
            return cleaned_count
        
        except Exception as e:
            logger.error(f"清理过期会话失败：{str(e)}")
            return 0

# 全局会话管理器实例
_session_manager = None

def get_session_manager() -> SessionManager:
    """获取全局会话管理器实例（单例模式）"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager