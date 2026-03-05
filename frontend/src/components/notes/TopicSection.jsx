/**
 * TopicSection component - Collapsible topic with subtopics and keywords
 * Requirements: 3.5, 9.4
 */

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import '../../styles/notes.css';

const TopicSection = ({ topic, defaultExpanded = false }) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleExpanded();
    }
  };

  return (
    <div className="topic-section" data-testid="topic-section">
      <button
        className={`topic-header ${isExpanded ? 'expanded' : ''}`}
        onClick={toggleExpanded}
        onKeyDown={handleKeyDown}
        aria-expanded={isExpanded}
        aria-controls={`topic-content-${topic.title.replace(/\s+/g, '-')}`}
        data-testid="topic-header"
      >
        <span className="text-h3 topic-title">{topic.title}</span>
        <span className="expand-icon" aria-hidden="true">
          {isExpanded ? '−' : '+'}
        </span>
      </button>

      {isExpanded && (
        <div
          id={`topic-content-${topic.title.replace(/\s+/g, '-')}`}
          className="topic-content"
          data-testid="topic-content"
        >
          {topic.content && (
            <div className="topic-main-content">
              <p className="text-body">{topic.content}</p>
            </div>
          )}

          {topic.subtopics && topic.subtopics.length > 0 && (
            <div className="subtopics">
              <h4>Subtopics</h4>
              <ul>
                {topic.subtopics.map((subtopic, index) => (
                  <li key={index}>{subtopic}</li>
                ))}
              </ul>
            </div>
          )}

          {topic.keywords && topic.keywords.length > 0 && (
            <div className="keywords">
              <h4>Keywords</h4>
              <div className="keyword-tags">
                {topic.keywords.map((keyword, index) => (
                  <span key={index} className="keyword-tag">
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}

          {topic.definitions && Object.keys(topic.definitions).length > 0 && (
            <div className="definitions">
              <h4>Definitions</h4>
              <dl>
                {Object.entries(topic.definitions).map(([term, definition]) => (
                  <div key={term} className="definition-item">
                    <dt>{term}</dt>
                    <dd>{definition}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {topic.formulas && topic.formulas.length > 0 && (
            <div className="formulas">
              <h4>Formulas</h4>
              <ul className="formula-list">
                {topic.formulas.map((formula, index) => (
                  <li key={index} className="formula-item">
                    <code>{formula}</code>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

TopicSection.propTypes = {
  topic: PropTypes.shape({
    title: PropTypes.string.isRequired,
    subtopics: PropTypes.arrayOf(PropTypes.string),
    keywords: PropTypes.arrayOf(PropTypes.string),
    definitions: PropTypes.objectOf(PropTypes.string),
    formulas: PropTypes.arrayOf(PropTypes.string),
    content: PropTypes.string,
  }).isRequired,
  defaultExpanded: PropTypes.bool,
};

export default TopicSection;
