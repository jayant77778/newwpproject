import React from 'react';
import { Search, X } from 'lucide-react';

/**
 * SearchInput Component
 * Reusable search input with clear functionality
 */
const SearchInput = ({ 
  value, 
  onChange, 
  placeholder = 'Search...', 
  className = '',
  onClear,
  disabled = false 
}) => {
  const handleClear = () => {
    onChange('');
    if (onClear) onClear();
  };

  return (
    <div className={`relative ${className}`}>
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <Search className="h-4 w-4 text-gray-400" />
      </div>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className={`
          form-input pl-10 pr-10
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      />
      {value && (
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
          <button
            onClick={handleClear}
            className="text-gray-400 hover:text-gray-600 focus:outline-none"
            disabled={disabled}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
};

export default SearchInput;
