# src/meta_prompt_agent/config/logging_config.py
import logging
import sys # 为了能够将日志输出到标准输出

def setup_logging(level=logging.INFO):
    """
    配置全局日志记录。

    Args:
        level (int, optional): 要设置的最低日志级别。默认为 logging.INFO。
    """
    # 创建一个logger，通常是根logger或者一个特定的应用logger
    # 如果我们获取根logger，那么所有子logger都会继承这个配置
    # logger = logging.getLogger() # 获取根logger
    # 或者，如果我们想为我们的应用创建一个顶层logger:
    logger = logging.getLogger('meta_prompt_agent') # 以我们的包名作为logger的顶层命名空间
    logger.setLevel(level)

    # 清除该logger上可能存在的任何现有处理器，以避免重复日志
    if logger.hasHandlers():
        logger.handlers.clear()

    # 创建一个处理器，用于将日志记录发送到标准输出 (控制台)
    # StreamHandler默认输出到sys.stderr，但我们可以指定sys.stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # 创建一个格式化器并将其添加到处理器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # 将处理器添加到logger
    logger.addHandler(console_handler)

    # （可选）如果你也想将日志输出到文件，可以添加FileHandler
    # file_handler = logging.FileHandler("app.log", mode='a', encoding='utf-8')
    # file_handler.setLevel(level)
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)

    # （可选）如果你希望其他模块通过 logging.getLogger(__name__) 获取的logger也使用这个配置
    # 那么配置根logger会更直接。但为应用创建一个顶层logger然后其他模块通过
    # logging.getLogger('meta_prompt_agent.module_name') 获取也是一种好方法。
    # 为了简单起见，并确保所有通过 getLogger(__name__) 获取的logger（如果它们的name以'meta_prompt_agent'开头）
    # 都能工作，我们可以配置根logger，或者确保我们所有模块都从 'meta_prompt_agent' 这个logger派生。

    # 让我们暂时采用配置根logger的方式，这样所有模块的logger都会继承这些设置。
    # 这种方式更接近 basicConfig 的行为，但更可控。
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[console_handler] # 使用我们创建的处理器
        # 如果也想输出到文件，可以加上 file_handler:
        # handlers=[console_handler, file_handler]
    )
    # basicConfig 只能调用一次。如果它已经被调用过，后续调用无效。
    # 因此，更健壮的方法是直接操作logger对象，如上面被注释掉的 logger.addHandler 部分。
    # 为了确保我们的配置生效并避免与Streamlit可能进行的任何默认日志配置冲突，
    # 让我们使用更明确的logger操作方式。

    # -- 修正后的推荐配置方式 --
    # 清理根logger的处理器，以防万一 (例如Streamlit可能已经添加了处理器)
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        for handler in root_logger.handlers[:]: # 迭代副本进行移除
            root_logger.removeHandler(handler)
            handler.close() # 关闭处理器

    # 现在为根logger配置我们的处理器
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    # if file_handler: # 如果你启用了文件处理器
    #     root_logger.addHandler(file_handler)

    # 记录一条信息表明日志已配置
    logging.getLogger(__name__).info("日志系统已配置。")


if __name__ == '__main__':
    # 用于测试 logging_config.py 本身
    setup_logging(logging.DEBUG)
    test_logger = logging.getLogger('meta_prompt_agent.test_module')
    test_logger.debug("这是一条来自测试模块的DEBUG信息。")
    test_logger.info("这是一条来自测试模块的INFO信息。")
    test_logger.warning("这是一条来自测试模块的WARNING信息。")
    logging.info("这是一条直接来自根logger的INFO信息（通过logging.info）。")

