-- Migration: Add layout_order column to presentations table
-- This allows each presentation to have a unique randomized layout order

ALTER TABLE presentations 
ADD COLUMN layout_order JSONB DEFAULT NULL;

-- Optional: Add an index for faster queries if needed
-- CREATE INDEX idx_presentations_layout_order ON presentations USING GIN (layout_order);

COMMENT ON COLUMN presentations.layout_order IS 'Randomized order of slide layouts for variety between presentations';
