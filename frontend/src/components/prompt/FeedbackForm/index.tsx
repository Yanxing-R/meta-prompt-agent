import React, { useState } from 'react';
import Button from '../../../components/common/Button';
import { StarIcon, StarFilledIcon } from '../../../components/icons';
import './styles.css';

interface FeedbackFormProps {
  promptId: string;
  originalRequest: string;
  generatedPrompt: string;
  onSubmit: (rating: number, comment: string) => Promise<void>;
  isSubmitting: boolean;
  submitSuccess?: boolean;
}

const FeedbackForm: React.FC<FeedbackFormProps> = ({
  promptId,
  originalRequest,
  generatedPrompt,
  onSubmit,
  isSubmitting,
  submitSuccess
}) => {
  const [rating, setRating] = useState<number>(0);
  const [comment, setComment] = useState<string>('');
  const [hoveredRating, setHoveredRating] = useState<number | null>(null);
  
  // 处理评分悬停
  const handleRatingHover = (hoverRating: number) => {
    setHoveredRating(hoverRating);
  };
  
  // 处理评分离开
  const handleRatingLeave = () => {
    setHoveredRating(null);
  };
  
  // 处理评分点击
  const handleRatingClick = (selectedRating: number) => {
    setRating(selectedRating);
  };
  
  // 处理表单提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(rating, comment);
  };
  
  // 渲染星级评分
  const renderStars = () => {
    const stars = [];
    
    for (let i = 1; i <= 5; i++) {
      const isActive = (hoveredRating !== null ? i <= hoveredRating : i <= rating);
      
      stars.push(
        <button
          key={i}
          type="button"
          className="rating-star-button"
          onClick={() => handleRatingClick(i)}
          onMouseEnter={() => handleRatingHover(i)}
          onMouseLeave={handleRatingLeave}
          aria-label={`${i} 星评分`}
        >
          {isActive ? <StarFilledIcon /> : <StarIcon />}
        </button>
      );
    }
    
    return stars;
  };
  
  // 获取评级文本
  const getRatingText = () => {
    const currentRating = hoveredRating !== null ? hoveredRating : rating;
    
    switch (currentRating) {
      case 1: return '很差';
      case 2: return '较差';
      case 3: return '一般';
      case 4: return '较好';
      case 5: return '很好';
      default: return '请评分';
    }
  };
  
  return (
    <div className="feedback-form-container">
      <h3 className="feedback-form-title">提交反馈</h3>
      <p className="feedback-form-description">
        您对生成的提示词质量满意吗？您的反馈将帮助我们改进系统。
      </p>
      
      {!submitSuccess ? (
        <form onSubmit={handleSubmit} className="feedback-form">
          <div className="feedback-rating-container">
            <span className="feedback-rating-label">质量评分:</span>
            <div className="star-rating-container">
              <div className="star-rating">
                {renderStars()}
              </div>
              <span className="rating-text">{getRatingText()}</span>
            </div>
          </div>
          
          <div className="feedback-comment-container">
            <label htmlFor="feedback-comment" className="feedback-comment-label">
              详细反馈 (可选):
            </label>
            <textarea
              id="feedback-comment"
              className="feedback-comment-textarea"
              placeholder="请输入您的具体建议或反馈..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </div>
          
          <div className="feedback-submit-container">
            <Button
              type="submit"
              variant="primary"
              disabled={rating === 0 || isSubmitting}
              isLoading={isSubmitting}
            >
              提交反馈
            </Button>
          </div>
        </form>
      ) : (
        <div className="feedback-success">
          <p className="feedback-success-message">
            感谢您的反馈！您的意见将帮助我们不断改进提示词优化功能。
          </p>
        </div>
      )}
    </div>
  );
};

export default FeedbackForm; 