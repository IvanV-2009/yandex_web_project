
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            reply_to INTEGER,
            new_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (reply_to) REFERENCES messages (id),
            FOREIGN KEY (new_id) REFERENCES news (id)
        );

        CREATE TABLE IF NOT EXISTS reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reaction_type TEXT CHECK(reaction_type IN ('like', 'dislike')),
            new_id INTEGER NOT NULL,
            FOREIGN KEY (message_id) REFERENCES messages (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (new_id) REFERENCES news (id),
            UNIQUE(message_id, user_id, new_id)
        );
        