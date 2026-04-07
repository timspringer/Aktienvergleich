import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

if (!supabaseUrl || !supabaseKey) {
  console.warn(
    'Missing Supabase configuration. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY'
  )
}

export const supabase = createClient(supabaseUrl, supabaseKey)

export async function getIndexes() {
  const { data, error } = await supabase.from('indices').select('*')
  if (error) throw error
  return data
}

export async function getCompanies(indexId: string) {
  const { data, error } = await supabase
    .from('companies')
    .select('*')
    .eq('index_id', indexId)
  if (error) throw error
  return data
}

export async function getEstimates(companyId: string) {
  const { data, error } = await supabase
    .from('estimates')
    .select('*')
    .eq('company_id', companyId)
    .order('fiscal_year', { ascending: true })
  if (error) throw error
  return data
}

export async function getMetrics(companyId: string) {
  const { data, error } = await supabase
    .from('metrics')
    .select('*')
    .eq('company_id', companyId)
    .single()
  if (error && error.code !== 'PGRST116') throw error
  return data
}
