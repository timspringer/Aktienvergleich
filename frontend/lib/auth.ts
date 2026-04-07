import { createContext, useContext } from 'react'
import { Session, User } from '@supabase/supabase-js'

export interface AuthContextType {
  session: Session | null
  user: User | null
  loading: boolean
  signUp: (email: string, password: string) => Promise<void>
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  isAuthenticated: boolean
}

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined
)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
