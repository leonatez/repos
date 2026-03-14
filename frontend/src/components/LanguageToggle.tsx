import { useLanguage } from '../contexts/LanguageContext'

interface LanguageToggleProps {
  className?: string
}

export default function LanguageToggle({ className = '' }: LanguageToggleProps) {
  const { language, setLanguage } = useLanguage()

  return (
    <div className={`flex items-center gap-1 bg-bg-secondary rounded-lg p-1 ${className}`}>
      <button
        onClick={() => setLanguage('vi')}
        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-200 ${
          language === 'vi'
            ? 'bg-accent text-bg-primary shadow-sm'
            : 'text-text-secondary hover:text-text-primary'
        }`}
        title="Tiếng Việt"
      >
        VI
      </button>
      <button
        onClick={() => setLanguage('en')}
        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-200 ${
          language === 'en'
            ? 'bg-accent text-bg-primary shadow-sm'
            : 'text-text-secondary hover:text-text-primary'
        }`}
        title="English"
      >
        EN
      </button>
    </div>
  )
}
