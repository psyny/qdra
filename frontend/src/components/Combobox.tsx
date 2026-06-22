import { useState, useRef, useEffect } from 'react';

type ComboboxProps = {
  value: string;
  onChange: (value: string) => void;
  options: string[];
  placeholder?: string;
  disabled?: boolean;
  style?: React.CSSProperties;
  className?: string;
};

export function Combobox({
  value,
  onChange,
  options,
  placeholder = 'Select or type...',
  disabled = false,
  style,
  className,
}: ComboboxProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState(value);
  const [filteredOptions, setFilteredOptions] = useState<string[]>(options);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  useEffect(() => {
    setFilteredOptions(options);
  }, [options]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInputValue(newValue);
    onChange(newValue);

    // Filter options based on input
    if (newValue) {
      const filtered = options.filter((opt) =>
        opt.toLowerCase().includes(newValue.toLowerCase())
      );
      setFilteredOptions(filtered);
      setIsOpen(true);
    } else {
      setFilteredOptions(options);
      setIsOpen(false);
    }
  };

  const handleOptionClick = (option: string) => {
    setInputValue(option);
    onChange(option);
    setIsOpen(false);
  };

  const handleFocus = () => {
    if (!disabled) {
      setIsOpen(true);
      setFilteredOptions(options);
    }
  };

  const handleBlur = (e: React.FocusEvent) => {
    // Delay closing to allow option clicks to register
    setTimeout(() => {
      setIsOpen(false);
    }, 200);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  return (
    <div ref={containerRef} style={{ position: 'relative', ...style }}>
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder}
        className={`form-input ${className || ''}`}
        style={{
          flex: 1,
          width: '100%',
          fontSize: '12px',
          padding: '5px 6px',
          ...style,
        }}
      />
      {isOpen && !disabled && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
            maxHeight: '200px',
            overflowY: 'auto',
            zIndex: 9999,
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
          }}
        >
          {filteredOptions.length === 0 ? (
            <div
              style={{
                padding: '8px',
                fontSize: '12px',
                color: '#8c8c8c',
                fontStyle: 'italic',
              }}
            >
              No matching options
            </div>
          ) : (
            filteredOptions.map((option, index) => (
              <div
                key={index}
                onClick={() => handleOptionClick(option)}
                onMouseDown={(e) => e.preventDefault()} // Prevent blur from firing before click
                style={{
                  padding: '8px 12px',
                  fontSize: '12px',
                  cursor: 'pointer',
                  color: '#f5f5f5',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.08)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                {option}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
