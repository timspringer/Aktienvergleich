import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export const runtime = 'nodejs'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const indexId = searchParams.get('indexId')
    const search = searchParams.get('search')
    const sortBy = searchParams.get('sortBy') || 'title'
    const sortOrder = searchParams.get('sortOrder') || 'asc'
    const limit = parseInt(searchParams.get('limit') || '50')
    const offset = parseInt(searchParams.get('offset') || '0')

    let query = supabase
      .from('companies')
      .select(
        `
        id,
        title,
        wkn,
        isin,
        last_scrape_status,
        indices(id, name, display_name, currency),
        estimates(
          fiscal_year,
          revenue_amount,
          dividend,
          dividend_yield_percent,
          eps,
          pe_ratio,
          avg_price_target
        ),
        metrics(
          revenue_cagr_percent,
          dividend_cagr_percent,
          dividend_yield_cagr_percent,
          eps_cagr_percent,
          pe_ratio_cagr_percent,
          estimate_count,
          first_estimate_year,
          last_estimate_year
        )
      `,
        { count: 'exact' }
      )

    // Filter by index
    if (indexId) {
      query = query.eq('index_id', indexId)
    }

    // Search by title, WKN, or ISIN
    if (search) {
      query = query.or(
        `title.ilike.%${search}%,wkn.ilike.%${search}%,isin.ilike.%${search}%`
      )
    }

    // Sort
    const validSortFields = ['title', 'wkn', 'isin', 'created_at']
    const sortField = validSortFields.includes(sortBy) ? sortBy : 'title'
    query = query.order(sortField, {
      ascending: sortOrder === 'asc',
    })

    // Pagination
    query = query.range(offset, offset + limit - 1)

    const { data, error, count } = await query

    if (error) {
      return NextResponse.json(
        { error: error.message },
        { status: 400 }
      )
    }

    return NextResponse.json({
      data: data || [],
      count: count || 0,
      limit,
      offset,
    })
  } catch (error) {
    console.error('Error fetching stocks:', error)
    return NextResponse.json(
      { error: 'Failed to fetch stocks' },
      { status: 500 }
    )
  }
}
