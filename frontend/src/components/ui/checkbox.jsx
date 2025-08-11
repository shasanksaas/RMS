import React from 'react';

const Checkbox = React.forwardRef(({ 
  className = '', 
  checked = false, 
  onCheckedChange,
  disabled = false,
  ...props 
}, ref) => {
  const handleChange = (e) => {
    if (onCheckedChange) {
      onCheckedChange(e.target.checked);
    }
  };

  return (
    <input
      type="checkbox"
      ref={ref}
      className={`h-4 w-4 rounded border border-gray-300 bg-white text-blue-600 focus:ring-blue-500 focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      checked={checked}
      onChange={handleChange}
      disabled={disabled}
      {...props}
    />
  );
});

Checkbox.displayName = 'Checkbox';

export { Checkbox };