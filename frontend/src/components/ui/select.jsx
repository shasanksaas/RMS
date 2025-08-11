import React, { useState, useRef, useEffect } from 'react';

const Select = ({ 
  children, 
  value, 
  onValueChange, 
  disabled = false,
  ...props 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const selectRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (selectRef.current && !selectRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleSelect = (selectedValue) => {
    if (onValueChange) {
      onValueChange(selectedValue);
    }
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={selectRef} {...props}>
      {React.Children.map(children, (child) => 
        React.cloneElement(child, { 
          isOpen, 
          setIsOpen, 
          value, 
          onSelect: handleSelect, 
          disabled 
        })
      )}
    </div>
  );
};

const SelectTrigger = React.forwardRef(({ 
  className = '', 
  children, 
  isOpen, 
  setIsOpen, 
  disabled,
  ...props 
}, ref) => (
  <button
    ref={ref}
    type="button"
    role="combobox"
    aria-expanded={isOpen}
    className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
    onClick={() => !disabled && setIsOpen(!isOpen)}
    disabled={disabled}
    {...props}
  >
    {children}
    <svg
      className={`h-4 w-4 opacity-50 transition-transform ${isOpen ? 'rotate-180' : ''}`}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <polyline points="6,9 12,15 18,9"></polyline>
    </svg>
  </button>
));

SelectTrigger.displayName = 'SelectTrigger';

const SelectValue = ({ placeholder, value, ...props }) => (
  <span className="pointer-events-none">
    {value || <span className="text-gray-500">{placeholder}</span>}
  </span>
);

const SelectContent = ({ 
  className = '', 
  children, 
  isOpen, 
  onSelect,
  ...props 
}) => {
  if (!isOpen) return null;

  return (
    <div
      className={`absolute top-full left-0 z-50 mt-1 w-full rounded-md border border-gray-200 bg-white shadow-md ${className}`}
      {...props}
    >
      <div className="py-1">
        {React.Children.map(children, (child) =>
          React.cloneElement(child, { onSelect })
        )}
      </div>
    </div>
  );
};

const SelectItem = React.forwardRef(({ 
  className = '', 
  children, 
  value, 
  onSelect,
  ...props 
}, ref) => (
  <button
    ref={ref}
    type="button"
    className={`relative flex w-full cursor-pointer select-none items-center py-2 px-3 text-sm outline-none hover:bg-gray-100 focus:bg-gray-100 ${className}`}
    onClick={() => onSelect && onSelect(value)}
    {...props}
  >
    {children}
  </button>
));

SelectItem.displayName = 'SelectItem';

export { Select, SelectContent, SelectItem, SelectTrigger, SelectValue };