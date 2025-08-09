import React, { useState, useRef, useEffect } from 'react';

const DropdownMenu = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={menuRef}>
      {React.Children.map(children, (child) =>
        React.cloneElement(child, { isOpen, setIsOpen })
      )}
    </div>
  );
};

const DropdownMenuTrigger = ({ children, asChild, isOpen, setIsOpen }) => {
  return (
    <div onClick={() => setIsOpen(!isOpen)}>
      {children}
    </div>
  );
};

const DropdownMenuContent = ({ children, className = "", align = "start", isOpen }) => {
  if (!isOpen) return null;

  const alignmentClasses = {
    start: 'left-0',
    end: 'right-0',
    center: 'left-1/2 transform -translate-x-1/2'
  };

  return (
    <div
      className={`absolute top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 py-1 ${alignmentClasses[align]} ${className}`}
    >
      {children}
    </div>
  );
};

const DropdownMenuItem = ({ children, onClick, className = "" }) => {
  return (
    <button
      className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 focus:bg-gray-50 focus:outline-none flex items-center ${className}`}
      onClick={onClick}
    >
      {children}
    </button>
  );
};

const DropdownMenuLabel = ({ children, className = "" }) => {
  return (
    <div className={`px-4 py-2 text-sm font-medium text-gray-900 ${className}`}>
      {children}
    </div>
  );
};

const DropdownMenuSeparator = () => {
  return <div className="border-t border-gray-200 my-1" />;
};

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
};