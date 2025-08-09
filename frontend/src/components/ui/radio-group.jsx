import React from 'react';

const RadioGroup = ({ children, value, onValueChange, className = "" }) => {
  return (
    <div className={`space-y-2 ${className}`} role="radiogroup">
      {React.Children.map(children, (child) =>
        React.cloneElement(child, { groupValue: value, onGroupChange: onValueChange })
      )}
    </div>
  );
};

const RadioGroupItem = ({ value, id, groupValue, onGroupChange, className = "" }) => {
  const isSelected = groupValue === value;
  
  return (
    <input
      type="radio"
      id={id}
      value={value}
      checked={isSelected}
      onChange={() => onGroupChange && onGroupChange(value)}
      className={`h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 ${className}`}
    />
  );
};

export { RadioGroup, RadioGroupItem };