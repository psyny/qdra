import { createContext, useContext, useState, ReactNode } from 'react';

export type MessageType = 'error' | 'warning' | 'info' | 'success';

interface Message {
  type: MessageType;
  content: string;
}

interface MessageContextType {
  message: Message | null;
  showMessage: (type: MessageType, content: string) => void;
  hideMessage: () => void;
}

const MessageContext = createContext<MessageContextType | undefined>(undefined);

export function MessageProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState<Message | null>(null);

  const showMessage = (type: MessageType, content: string) => {
    setMessage({ type, content });
  };

  const hideMessage = () => {
    setMessage(null);
  };

  return (
    <MessageContext.Provider value={{ message, showMessage, hideMessage }}>
      {children}
    </MessageContext.Provider>
  );
}

export function useMessageContext() {
  const context = useContext(MessageContext);
  if (context === undefined) {
    throw new Error('useMessageContext must be used within a MessageProvider');
  }
  return context;
}
