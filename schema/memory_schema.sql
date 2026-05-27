-- Phase 6: Memory + Adaptive Learning Database Schema
-- PostgreSQL schema for production deployment
-- Requires: PostgreSQL 12+, pgvector extension

-- ================================================================
-- ENABLE EXTENSIONS
-- ================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For full-text search


-- ================================================================
-- USER PROFILES TABLE
-- ================================================================

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id VARCHAR(255) PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    learning_style VARCHAR(50),  -- visual, code, text, examples, socratic, mixed
    preferred_tone VARCHAR(50),  -- hinglish, formal, casual, etc
    total_sessions INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    average_distress FLOAT DEFAULT 0.0,
    last_active TIMESTAMP DEFAULT NOW(),
    
    -- Metadata
    created_by VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_learning_style CHECK (learning_style IN ('visual', 'code', 'text', 'examples', 'socratic', 'mixed')),
    INDEX idx_user_last_active (last_active DESC)
);


-- ================================================================
-- CONVERSATIONS TABLE
-- ================================================================

CREATE TABLE IF NOT EXISTS conversations (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    
    primary_topic VARCHAR(255),
    topics TEXT ARRAY,  -- Array of topics discussed
    summary TEXT,
    
    -- Metrics
    message_count INTEGER DEFAULT 0,
    avg_distress FLOAT DEFAULT 0.0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_conversations (user_id, created_at DESC),
    INDEX idx_conversation_date (created_at DESC),
    INDEX idx_conversation_primary_topic (primary_topic)
);


-- ================================================================
-- MESSAGES TABLE (with embeddings for semantic search)
-- ================================================================

CREATE TABLE IF NOT EXISTS messages (
    message_id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL REFERENCES conversations(session_id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    role VARCHAR(50) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    
    -- Analysis
    tone VARCHAR(50),  -- confused, confident, frustrated, etc
    distress_level FLOAT,  -- 0-1
    topics TEXT ARRAY,  -- Topics mentioned in message
    
    -- Embeddings for semantic search
    embedding vector(384),  -- sentence-transformers/all-MiniLM-L6-v2
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_role CHECK (role IN ('user', 'assistant')),
    CONSTRAINT valid_distress CHECK (distress_level BETWEEN 0 AND 1),
    INDEX idx_user_messages (user_id, created_at DESC),
    INDEX idx_session_messages (session_id, created_at),
    INDEX idx_message_topic (topics),
    INDEX idx_message_embedding ON messages USING ivfflat (embedding vector_cosine_ops)
);


-- ================================================================
-- TOPIC MASTERY TABLE
-- ================================================================

CREATE TABLE IF NOT EXISTS topic_mastery (
    mastery_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    
    -- Confidence & Performance
    confidence FLOAT NOT NULL DEFAULT 0.0,  -- 0-1
    attempts INTEGER DEFAULT 0,
    successes INTEGER DEFAULT 0,
    failures INTEGER DEFAULT 0,
    
    -- Timing
    first_attempt TIMESTAMP,
    last_attempt TIMESTAMP,
    date_mastered TIMESTAMP,  -- When confidence >= 0.8
    
    -- Learning analytics
    learning_velocity FLOAT,  -- confidence gained per day
    misconceptions TEXT ARRAY,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_confidence CHECK (confidence BETWEEN 0 AND 1),
    CONSTRAINT unique_user_topic UNIQUE (user_id, topic),
    INDEX idx_user_topic (user_id, confidence DESC),
    INDEX idx_topic_date_mastered (topic, date_mastered),
    INDEX idx_user_mastered (user_id, date_mastered DESC)
);


-- ================================================================
-- LEARNING INTERACTIONS TABLE
-- ================================================================

CREATE TABLE IF NOT EXISTS learning_interactions (
    interaction_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    
    -- Interaction details
    interaction_type VARCHAR(50) NOT NULL,  -- success, struggle, confusion, incorrect, partial, mastery
    difficulty_rating INTEGER,  -- 1-5
    misconception TEXT,
    explanation TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_interaction CHECK (interaction_type IN ('success', 'struggle', 'confusion', 'incorrect', 'partial', 'mastery')),
    CONSTRAINT valid_difficulty CHECK (difficulty_rating IS NULL OR difficulty_rating BETWEEN 1 AND 5),
    INDEX idx_user_interactions (user_id, created_at DESC),
    INDEX idx_topic_interactions (topic, created_at DESC),
    INDEX idx_interaction_type (interaction_type)
);


-- ================================================================
-- RECOMMENDATIONS TABLE
-- ================================================================

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    -- Recommendation details
    recommended_topic VARCHAR(255) NOT NULL,
    priority FLOAT NOT NULL,  -- 0-1
    reason TEXT NOT NULL,
    difficulty_level VARCHAR(50),  -- easy, medium, hard
    estimated_time_minutes INTEGER,
    
    -- Recommendation status
    status VARCHAR(50) DEFAULT 'pending',  -- pending, accepted, completed, skipped
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'accepted', 'completed', 'skipped')),
    INDEX idx_user_recommendations (user_id, status)
);


-- ================================================================
-- SESSION SUMMARIES TABLE
-- ================================================================

CREATE TABLE IF NOT EXISTS session_summaries (
    summary_id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE REFERENCES conversations(session_id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    -- Summary content
    executive_summary TEXT NOT NULL,
    key_learnings TEXT ARRAY,
    misconceptions TEXT ARRAY,
    
    -- Analytics
    productivity_score FLOAT,  -- 0-1
    emotional_journey TEXT,
    learning_style_indicators TEXT ARRAY,
    
    -- Recommendations
    recommendations TEXT ARRAY,
    next_steps TEXT ARRAY,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_summaries (user_id, created_at DESC)
);


-- ================================================================
-- MEMORY VECTORS TABLE (for semantic memory retrieval)
-- ================================================================

CREATE TABLE IF NOT EXISTS memory_vectors (
    memory_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    -- Memory content
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    
    -- Semantic representation
    embedding vector(384),
    
    -- Access tracking
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    relevance_score FLOAT DEFAULT 1.0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_memories (user_id, created_at DESC),
    INDEX idx_memory_embedding ON memory_vectors USING ivfflat (embedding vector_cosine_ops)
);


-- ================================================================
-- ANALYTICS TABLE
-- ================================================================

CREATE TABLE IF NOT EXISTS user_analytics (
    analytics_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE REFERENCES user_profiles(user_id) ON DELETE CASCADE,
    
    -- Engagement
    total_queries INTEGER DEFAULT 0,
    total_conversation_time INTEGER DEFAULT 0,  -- minutes
    sessions_count INTEGER DEFAULT 0,
    
    -- Learning
    topics_attempted INTEGER DEFAULT 0,
    topics_mastered INTEGER DEFAULT 0,
    mastery_rate FLOAT DEFAULT 0.0,
    
    -- Velocity
    learning_rate FLOAT DEFAULT 0.0,  -- topics per week
    average_confidence FLOAT DEFAULT 0.0,
    
    -- Trends
    distress_trend VARCHAR(50),  -- escalating, stable, improving
    last_summary TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_analytics_mastery (topics_mastered DESC),
    INDEX idx_analytics_velocity (learning_rate DESC)
);


-- ================================================================
-- VIEWS (for easier querying)
-- ================================================================

-- User learning progress view
CREATE VIEW IF NOT EXISTS user_learning_progress AS
SELECT
    u.user_id,
    u.created_at,
    COUNT(DISTINCT tm.topic) as topics_attempted,
    SUM(CASE WHEN tm.confidence >= 0.8 THEN 1 ELSE 0 END) as topics_mastered,
    AVG(tm.confidence) as avg_confidence,
    AVG(tm.learning_velocity) as avg_learning_velocity,
    MAX(tm.last_attempt) as last_learning_activity
FROM user_profiles u
LEFT JOIN topic_mastery tm ON u.user_id = tm.user_id
GROUP BY u.user_id, u.created_at;


-- Active sessions view
CREATE VIEW IF NOT EXISTS active_sessions AS
SELECT
    c.session_id,
    c.user_id,
    c.start_time,
    COUNT(m.message_id) as message_count,
    MAX(m.created_at) as last_message_time,
    NOW() - c.start_time as duration
FROM conversations c
LEFT JOIN messages m ON c.session_id = m.session_id
WHERE c.end_time IS NULL
GROUP BY c.session_id, c.user_id, c.start_time;


-- ================================================================
-- INDEXES FOR PERFORMANCE
-- ================================================================

-- Composite indexes
CREATE INDEX IF NOT EXISTS idx_user_topic_date ON topic_mastery(user_id, topic, date_mastered DESC);
CREATE INDEX IF NOT EXISTS idx_messages_user_session ON messages(user_id, session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_interactions_user_topic ON learning_interactions(user_id, topic, created_at DESC);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_message_content_search ON messages USING GIN (
    to_tsvector('english', content)
);


-- ================================================================
-- FUNCTIONS & TRIGGERS
-- ================================================================

-- Function to update user last_active
CREATE OR REPLACE FUNCTION update_user_last_active()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_profiles SET last_active = NOW() WHERE user_id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update last_active on new message
CREATE TRIGGER trg_update_last_active AFTER INSERT ON messages
FOR EACH ROW EXECUTE FUNCTION update_user_last_active();

-- Function to calculate learning velocity
CREATE OR REPLACE FUNCTION calculate_learning_velocity(p_user_id VARCHAR, p_topic VARCHAR)
RETURNS FLOAT AS $$
DECLARE
    v_first_date TIMESTAMP;
    v_last_date TIMESTAMP;
    v_days_elapsed INTEGER;
    v_confidence FLOAT;
BEGIN
    SELECT MIN(created_at), MAX(created_at), COUNT(*)
    INTO v_first_date, v_last_date, v_days_elapsed
    FROM learning_interactions
    WHERE user_id = p_user_id AND topic = p_topic;
    
    IF v_first_date IS NULL THEN
        RETURN 0.0;
    END IF;
    
    v_days_elapsed := EXTRACT(DAY FROM (v_last_date - v_first_date)) + 1;
    
    SELECT confidence INTO v_confidence
    FROM topic_mastery
    WHERE user_id = p_user_id AND topic = p_topic;
    
    RETURN v_confidence / v_days_elapsed;
END;
$$ LANGUAGE plpgsql;


-- ================================================================
-- INITIALIZATION DATA
-- ================================================================

-- Sample topics hierarchy
INSERT INTO topic_mastery (mastery_id, user_id, topic, confidence)
VALUES
    (gen_random_uuid()::text, 'sample_user', 'if-statements', 0.5),
    (gen_random_uuid()::text, 'sample_user', 'loops', 0.6),
    (gen_random_uuid()::text, 'sample_user', 'functions', 0.4)
ON CONFLICT (user_id, topic) DO NOTHING;


-- ================================================================
-- NOTES FOR PRODUCTION
-- ================================================================

/*
1. Connect pgvector for semantic search:
   - RECOMMEND: Exact match KNN search on embeddings
   - PARAMETERS: Lists 20, Probes 10 (balance speed/recall)

2. Indexing strategy:
   - HOT tables: conversations, messages, learning_interactions
   - Archive old records (>1 year) to separate partitions

3. Backup strategy:
   - Daily snapshots to S3
   - Point-in-time recovery enabled

4. Monitoring:
   - Track query performance on embedding search
   - Monitor disk space (vector embeddings take space)
   - Alert on missing_data ratio

5. Data retention:
   - Keep all memories indefinitely (they get better with age!)
   - Archive conversations >6 months
   - Keep analytics forever

6. Scale considerations:
   - Partition messages by user_id for large deployments
   - Use read replicas for analytics queries
   - Cache popular user profiles in Redis
*/
