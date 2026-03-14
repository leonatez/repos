import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export default function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  return (
    <div className={`prose prose-invert max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-3xl font-bold text-text-primary mt-8 mb-4 first:mt-0">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-2xl font-bold text-text-primary mt-8 mb-4 border-b border-border pb-2">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-xl font-semibold text-text-primary mt-6 mb-3">{children}</h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-lg font-semibold text-text-primary mt-4 mb-2">{children}</h4>
          ),
          p: ({ children }) => (
            <p className="text-slate-300 leading-relaxed mb-4">{children}</p>
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent hover:text-accent-light underline underline-offset-2 transition-colors"
            >
              {children}
            </a>
          ),
          code: ({ className, children, ...props }) => {
            const isBlock = className?.includes('language-')
            if (isBlock) {
              return (
                <code
                  className={`block bg-bg-secondary border border-border rounded-lg p-4 text-sm font-mono text-teal-300 overflow-x-auto ${className}`}
                  {...props}
                >
                  {children}
                </code>
              )
            }
            return (
              <code
                className="px-1.5 py-0.5 bg-bg-tertiary text-teal-300 font-mono text-sm rounded border border-border"
                {...props}
              >
                {children}
              </code>
            )
          },
          pre: ({ children }) => (
            <pre className="bg-bg-secondary border border-border rounded-xl p-4 overflow-x-auto my-4 text-sm">
              {children}
            </pre>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-accent pl-4 py-1 my-4 text-text-secondary italic bg-accent/5 rounded-r-lg">
              {children}
            </blockquote>
          ),
          ul: ({ children }) => (
            <ul className="list-none space-y-1 mb-4 ml-0">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-inside space-y-1 mb-4 ml-0 text-slate-300">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="text-slate-300 flex items-start gap-2">
              <span className="text-accent mt-1 shrink-0">•</span>
              <span>{children}</span>
            </li>
          ),
          strong: ({ children }) => (
            <strong className="text-text-primary font-semibold">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="text-text-secondary italic">{children}</em>
          ),
          hr: () => <hr className="border-border my-8" />,
          table: ({ children }) => (
            <div className="overflow-x-auto my-4">
              <table className="w-full border-collapse border border-border text-sm">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-bg-tertiary">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="border border-border px-4 py-2 text-left text-text-primary font-semibold">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-border px-4 py-2 text-slate-300">{children}</td>
          ),
          img: ({ src, alt }) => (
            <img
              src={src}
              alt={alt}
              className="rounded-xl max-w-full h-auto my-4 border border-border"
            />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
