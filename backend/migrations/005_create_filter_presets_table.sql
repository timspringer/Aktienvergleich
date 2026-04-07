-- Create filter_presets table for user-saved stock filters
CREATE TABLE IF NOT EXISTS filter_presets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  index_id UUID NOT NULL REFERENCES indices(id) ON DELETE CASCADE,

  name VARCHAR(255) NOT NULL,
  description TEXT,

  -- Filter configuration stored as JSON
  -- Example: {"min_pe": 10, "max_pe": 25, "min_revenue_cagr": 5}
  filter_config JSONB NOT NULL DEFAULT '{}'::JSONB,

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX idx_filter_presets_user_id ON filter_presets(user_id);
CREATE INDEX idx_filter_presets_index_id ON filter_presets(index_id);
CREATE INDEX idx_filter_presets_user_index ON filter_presets(user_id, index_id);

-- Add comments
COMMENT ON TABLE filter_presets IS 'User-saved filter configurations for stock screening';
COMMENT ON COLUMN filter_presets.user_id IS 'Reference to authenticated user';
COMMENT ON COLUMN filter_presets.index_id IS 'Index this preset applies to';
COMMENT ON COLUMN filter_presets.filter_config IS 'JSON configuration with filter criteria';
