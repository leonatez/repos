import React, { createContext, useContext, useState, useEffect } from 'react'
import { Language } from '../types'

interface LanguageContextValue {
  language: Language
  setLanguage: (lang: Language) => void
  toggle: () => void
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined)

const STORAGE_KEY = 'ai-digest-language'

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    return (localStorage.getItem(STORAGE_KEY) as Language) || 'vi'
  })

  const setLanguage = (lang: Language) => {
    setLanguageState(lang)
    localStorage.setItem(STORAGE_KEY, lang)
  }

  const toggle = () => {
    setLanguage(language === 'vi' ? 'en' : 'vi')
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, toggle }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}
