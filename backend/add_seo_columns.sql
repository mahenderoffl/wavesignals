"""
SQL script to add missing SEO columns to posts table
Run this in Neon SQL editor or via psql
"""

ALTER TABLE posts ADD COLUMN IF NOT EXISTS meta_description TEXT;
ALTER TABLE posts ADD COLUMN IF NOT EXISTS keywords TEXT;
ALTER TABLE posts ADD COLUMN IF NOT EXISTS hashtags TEXT;
ALTER TABLE posts ADD COLUMN IF NOT EXISTS search_queries TEXT;
