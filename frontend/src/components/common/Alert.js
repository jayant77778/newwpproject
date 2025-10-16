import React from 'react';
import { AlertCircle, CheckCircle, Info, XCircle } from 'lucide-react';

/**
 * Alert Component
 * Displays different types of alerts (success, error, warning, info)
 */
const Alert = ({ 
  type = 'info', 
  title, 
  message, 
  onClose, 
  className = '',
  actions 
}) => {
  const alertStyles = {
    success: {
      container: 'bg-success-50 border-success-200 dark:bg-success-900 dark:border-success-700',
      icon: <CheckCircle className="w-5 h-5 text-success-600" />,
      title: 'text-success-800 dark:text-success-200',
      message: 'text-success-700 dark:text-success-300'
    },
    error: {
      container: 'bg-error-50 border-error-200 dark:bg-error-900 dark:border-error-700',
      icon: <XCircle className="w-5 h-5 text-error-600" />,
      title: 'text-error-800 dark:text-error-200',
      message: 'text-error-700 dark:text-error-300'
    },
    warning: {
      container: 'bg-warning-50 border-warning-200 dark:bg-warning-900 dark:border-warning-700',
      icon: <AlertCircle className="w-5 h-5 text-warning-600" />,
      title: 'text-warning-800 dark:text-warning-200',
      message: 'text-warning-700 dark:text-warning-300'
    },
    info: {
      container: 'bg-primary-50 border-primary-200 dark:bg-primary-900 dark:border-primary-700',
      icon: <Info className="w-5 h-5 text-primary-600" />,
      title: 'text-primary-800 dark:text-primary-200',
      message: 'text-primary-700 dark:text-primary-300'
    }
  };

  const style = alertStyles[type];

  return (
    <div className={`
      border rounded-lg p-4 animate-fade-in
      ${style.container}
      ${className}
    `}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {style.icon}
        </div>
        <div className="ml-3 flex-1">
          {title && (
            <h3 className={`text-sm font-medium ${style.title}`}>
              {title}
            </h3>
          )}
          {message && (
            <p className={`text-sm ${title ? 'mt-1' : ''} ${style.message}`}>
              {message}
            </p>
          )}
          {actions && (
            <div className="mt-3 flex space-x-2">
              {actions}
            </div>
          )}
        </div>
        {onClose && (
          <div className="ml-auto pl-3">
            <button
              onClick={onClose}
              className={`
                inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2
                ${style.title} hover:bg-black hover:bg-opacity-10
              `}
            >
              <XCircle className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Alert;
