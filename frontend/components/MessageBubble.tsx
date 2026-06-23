import React from 'react';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ role, content, sources }) => {
  const renderContent = (text: string) => {
    const markdownRegex = /(\*\*(.*?)\*\*)|(`(.*?)`)|(```([\s\S]*?)```)/g;
    const parts = text.split(markdownRegex);

    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={index} className="font-bold">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={index} className="bg-gray-200 text-sm px-1 rounded">
            {part.slice(1, -1)}
          </code>
        );
      }
      if (part.startsWith('```') && part.endsWith('```')) {
        return (
          <pre key={index} className="bg-gray-100 text-sm p-2 rounded">
            {part.slice(3, -3)}
          </pre>
        );
      }
      return part;
    });
  };

  const handleSourceClick = (source: string) => {
    navigator.clipboard.writeText(source).catch(() => {
      alert('Failed to copy source text.');
    });
  };

  return (
    <div
      className={`flex ${
        role === 'user' ? 'justify-end' : 'justify-start'
      } mb-4`}
    >
      <div
        className={`max-w-md p-3 rounded-lg ${
          role === 'user'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-200 text-black'
        }`}
      >
        <div>{renderContent(content)}</div>
        {role === 'assistant' && sources && sources.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {sources.map((source, index) => (
              <button
                key={index}
                onClick={() => handleSourceClick(source)}
                className="text-xs bg-gray-300 px-2 py-1 rounded hover:bg-gray-400"
              >
                {source}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;