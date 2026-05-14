import aiosqlite

DB_PATH = "fitbot.db"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    gender      TEXT    NOT NULL,
    age         INTEGER NOT NULL,
    height      INTEGER NOT NULL,
    weight      REAL    NOT NULL,
    goal        TEXT    NOT NULL,
    activity    TEXT    NOT NULL,
    restrictions TEXT   NOT NULL DEFAULT 'none',
    preferences  TEXT   NOT NULL DEFAULT 'none',
    target_calories INTEGER NOT NULL,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE)
        await db.commit()


async def save_user(user_id: int, profile: dict) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users
                (user_id, name, gender, age, height, weight, goal, activity,
                 restrictions, preferences, target_calories, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                name             = excluded.name,
                gender           = excluded.gender,
                age              = excluded.age,
                height           = excluded.height,
                weight           = excluded.weight,
                goal             = excluded.goal,
                activity         = excluded.activity,
                restrictions     = excluded.restrictions,
                preferences      = excluded.preferences,
                target_calories  = excluded.target_calories,
                updated_at       = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                profile["name"],
                profile["gender"],
                profile["age"],
                profile["height"],
                profile["weight"],
                profile["goal"],
                profile["activity"],
                profile["restrictions"],
                profile["preferences"],
                profile["target_calories"],
            ),
        )
        await db.commit()


async def get_all_users() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
    if row is None:
        return None
    return dict(row)
