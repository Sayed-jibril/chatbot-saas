-- Create database
CREATE DATABASE chatbot_saas;
USE chatbot_saas;

-- Users table
CREATE TABLE users (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    plan_type ENUM('free', 'pro', 'business') DEFAULT 'free',
    tokens_used INT DEFAULT 0,
    token_limit INT DEFAULT 10000
);

-- Bots table
CREATE TABLE bots (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    api_key CHAR(64) UNIQUE NOT NULL,
    welcome_message TEXT DEFAULT 'Hello! How can I help you?',
    primary_color VARCHAR(20) DEFAULT '#3B82F6',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_api_key (api_key)
);

-- Documents table (BLOB storage)
CREATE TABLE documents (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    bot_id CHAR(36) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_data LONGBLOB NOT NULL,
    file_size INT NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    INDEX idx_bot_id (bot_id),
    INDEX idx_processed (processed)
);

-- Embeddings table (JSON storage)
CREATE TABLE embeddings (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    bot_id CHAR(36) NOT NULL,
    document_id CHAR(36) NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding JSON NOT NULL,
    chunk_index INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_bot_id (bot_id),
    INDEX idx_document_id (document_id),
    FULLTEXT INDEX idx_chunk_text (chunk_text)
);

-- Conversations table (for analytics)
CREATE TABLE conversations (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    bot_id CHAR(36) NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    visitor_ip VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE,
    INDEX idx_bot_session (bot_id, session_id)
);

-- Messages table
CREATE TABLE messages (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    conversation_id CHAR(36) NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    tokens_used INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    INDEX idx_conversation (conversation_id)
);

-- Create default admin user (password: admin123 - change in production)
INSERT INTO users (id, name, email, password_hash, plan_type) 
VALUES (
    UUID(),
    'Admin',
    'admin@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2c2dOg1Kuy', -- admin123
    'business'
);