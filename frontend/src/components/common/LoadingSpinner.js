import React from 'react';

/**
 * LoadingSpinner Component
 * Displays a spinning loader with optional text
 */
const LoadingSpinner = ({ size = 'md', text = 'Loading...', className = '' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  return (
    <div className={`flex flex-col items-center justify-center p-8 ${className}`}>
      <div className={`spinner ${sizeClasses[size]} mb-4`}></div>
      {text && (
        <p className="text-gray-600 dark:text-gray-400 text-sm animate-pulse">
          {text}
        </p>
      )}
    </div>
  );
};

export default LoadingSpinner;
