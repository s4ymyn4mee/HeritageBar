const express = require("express");
const { Pool } = require("pg");
const dbConfig = require('./dbConfig');
const helmet = require("helmet"); 
const session = require("express-session");
const PgSession = require("connect-pg-simple")(session);
const bcrypt = require("bcrypt");
const app = express();
const path = require("path");
const PORT = 3000;
const PEOPLE_AMOUNT = 5;
const TABLE_AMOUNT = 10;

app.set("view engine", "ejs");
// настроил Content Security Policy (CSP) с помощью Helmet для защиты от XSS и других атак
app.use(
  helmet.contentSecurityPolicy({
    useDefaults: true,
    directives: {
      defaultSrc: ["'self'"], //  разрешает загрузку ресурсов только с того же домена.
      scriptSrc: ["'self'"], // разрешает загрузку JavaScript только с того же домена.
      styleSrc: ["'self'", "https://fonts.googleapis.com"], // пример разрешения загрузки стилей и шрифтов с доменов Google Fonts.
      imgSrc: ["'self'", "data:"], // разрешает изображения с моего домена и данные, встроенные в base64.
      connectSrc: ["'self'"],
      objectSrc: ["'none'"], // отключает загрузку плагинов
      upgradeInsecureRequests: [], // директива, указывает браузеру обновлять HTTP-запросы до HTTPS.
    },
  })
);
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.urlencoded({ extended: false }));

const pool = new Pool(dbConfig);

app.use(
  session({
    store: new PgSession({
      pool: pool,
      tableName: 'session'
    }),
    secret: "mySecret",
    resave: false,
    saveUninitialized: false,
    cookie: {
      maxAge: 7 * 24 * 60 * 60 * 1000, // 7 дней
      secure: false, // true, если HTTPS, иначе false
      httpOnly: true,
      sameSite: 'lax'
    },
  })
);

pool
  .connect()
  .then(() => console.log("Connected to PostgreSQL successfully"))
  .catch((err) => console.error("Connection error", err.stack));

let orders = new Map();

app.get("/", (req, res) => {
  res.render("index.ejs");
});

app.post("/", (req, res) => {
  res.render("index.ejs");
});

app.get("/profile", async (req, res) => {
  if (!req.session.username) {
    return res.redirect("/login");
  }

  try {
    const userResult = await pool.query(
      `SELECT
        people_count,
        table_id, 
        TO_CHAR(date, 'DD.MM.YYYY') AS formatted_date,
        TO_CHAR(time, 'HH24:MI') AS formatted_time
      FROM ganiev.reserved_tables
      JOIN ganiev.users ON ganiev.users.user_id = ganiev.reserved_tables.user_id
      WHERE ganiev.users.user_id = $1`,
      [req.session.userId]
    );

    if (!userResult.rows) {
      return res.redirect("/login");
    }

    const allUserReservations = userResult.rows.map(row => ({
      peopleCount: row.people_count,
      tableNumber: row.table_id,
      date: row.formatted_date,
      time: row.formatted_time
    }));

    orders.set(req.session.email, allUserReservations);

    res.render("profile.ejs", { orders: orders.get(req.session.email) });
  } catch (error) {
    console.error("Ошибка поиска столиков:\n", error);
    res.sendStatus(500);
  }
});

app.get("/menu", (req, res) => {
  res.render("menu.ejs");
});

app.get("/reservation", (req, res) => {
  const options = {
    timeZone: 'Asia/Yekaterinburg',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  };

  // Формат YYYY-MM-DD
  const formattedDate = new Intl.DateTimeFormat('en-CA', options).format(new Date()); 
  const reservationErrorMessage = req.session.reservationErrorMessage || "";

  req.session.reservationErrorMessage = "";

  if (req.session.username) {
    res.render("reservation.ejs", { 
      currentDate: formattedDate,
      errorReservation: reservationErrorMessage,
      peopleAmount: PEOPLE_AMOUNT,
      tableAmount: TABLE_AMOUNT
     });
  }
  else { res.redirect("/login"); }
});

app.post("/reservation", async (req, res) => {
  const {peopleCount, tableNumber, date, time} = req.body;

  if (peopleCount <= 0 || peopleCount > PEOPLE_AMOUNT) {
    req.session.reservationErrorMessage = "Некорректное число человек";
    return res.redirect("/reservation");
  }

  if (tableNumber <= 0 || tableNumber > TABLE_AMOUNT) {
    req.session.reservationErrorMessage = "Некорректный номер столика";
    return res.redirect("/reservation");
  }

  const datePattern = /^20\d{2}-\d{2}-\d{2}$/; // YYYY-MM-DD
  if (!datePattern.test(date)) {
    req.session.reservationErrorMessage = "Некорректный формат даты бронирования";

    return res.redirect("/reservation");
  }

  const timePattern = /^([01]\d|2[0-3]):([0-5]\d)$/; // HH:MM (00:00 - 23:59)
  if (!timePattern.test(time)) {
    req.session.reservationErrorMessage = "Некорректный формат времени бронирования";

    return res.redirect("/reservation");
  }

  const bookingDateTime = new Date(`${date}T${time}:00`);
  const now = new Date();
  if (bookingDateTime <= now) {
    req.session.reservationErrorMessage = "Дата и время бронирования уже прошли";

    return res.redirect("/reservation");
  }

  const reservationHour = bookingDateTime.getHours();
  if (!(reservationHour >= 18 && reservationHour <= 23 || reservationHour >= 0 && reservationHour < 6)) {
    req.session.reservationErrorMessage = "Бронирование возможно только с 18:00 до 05:59";

    return res.redirect("/reservation");
  }

  try {
    const reservationCheck = await pool.query(
      `SELECT * FROM ganiev.reserved_tables 
      WHERE table_id = $1
      AND   date = $2
      AND   time = $3`,
      [tableNumber, date, time]
    );

    if (reservationCheck.rows.length > 0) {
      req.session.reservationErrorMessage = "Столик уже занят";

      return res.redirect("/reservation");
    }

    const insertReservationQuery = `
      INSERT INTO ganiev.reserved_tables (user_id, 
      table_id, 
      username,
      email, 
      date,
      time,
      people_count
      ) 
      VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING user_id
    `;
    await pool.query(insertReservationQuery, [
      req.session.userId,
      tableNumber,
      req.session.username,
      req.session.email,
      date,
      time,
      peopleCount
    ]);

    req.session.reservationErrorMessage = "";

    return res.redirect("/profile");
  } catch (error) {
    console.error("Ошибка бронирования столика:\n", error);
    res.sendStatus(500);
  }
});

app.get("/login", (req, res) => {
  const errorEmailMessage = req.session.emailErrorMessage || "";
  const errorPasswordMessage = req.session.passwordErrorMessage || "";

  req.session.emailErrorMessage = "";
  req.session.passwordErrorMessage = "";

  res.render("login.ejs", {
    errorEmail: errorEmailMessage,
    errorPassword: errorPasswordMessage,
  });
});

app.post("/login", async (req, res) => {
  const { email, password } = req.body;

  const emailPattern = /^[a-zA-Z0-9._%+-]{1,50}@[a-zA-Z0-9.-]{1,50}.[a-zA-Z]{2,}$/;
  if (!emailPattern.test(email)) {
    req.session.emailErrorMessage = "Некорректный email";

    return res.redirect("/login");
  }

  const passwordPattern = /^[^\s]{8,50}$/;
  if (!passwordPattern.test(password)) {
    req.session.passwordErrorMessage = "Неверный пароль";

    return res.redirect("/login");
  }

  try {
    const userResult = await pool.query(
      `SELECT * FROM ganiev.users WHERE email = $1`,
      [email]
    );

    const user = userResult.rows[0];
    if (!user) {
      req.session.emailErrorMessage = "Несуществующий email";

      return res.redirect("/login");
    }

    const passwordMatch = await bcrypt.compare(password, user.password);
    if (passwordMatch) {
      req.session.userId = user.user_id;
      req.session.username = user.username;
      req.session.email = user.email;

      return res.redirect("/profile");
    } else {
      req.session.passwordErrorMessage = "Неверный пароль";

      return res.redirect("/login");
    }
  } catch (error) {
    console.error("Ошибка авторизации:\n", error);
    res.sendStatus(500);
  }
});

app.get("/register", (req, res) => {
  const errorEmailMessage = req.session.emailErrorMessage || "";
  const errorUsernameMessage = req.session.usernameErrorMessage || "";
  const errorPasswordMessage = req.session.passwordErrorMessage || "";

  req.session.emailErrorMessage = "";
  req.session.usernameErrorMessage = "";
  req.session.passwordErrorMessage = "";

  res.render("register.ejs", {
    errorUsername: errorUsernameMessage,
    errorEmail: errorEmailMessage,
    errorPassword: errorPasswordMessage
  });
});

app.post("/register", async (req, res) => {
  const { username, email, password } = req.body;

  const usernamePattern = /^[a-zA-Zа-яА-Я\s]{2,50}$/;
  if (!usernamePattern.test(username)) {
    req.session.usernameErrorMessage = "Допускается только латиница, кириллица и пробел";

    return res.redirect("/register");
  }

  const emailPattern = /^[a-zA-Z0-9._%+-]{1,50}@[a-zA-Z0-9.-]{1,50}.[a-zA-Z]{2,}$/;
  if (!emailPattern.test(email)) {
    req.session.emailErrorMessage = "Некорректный email";

    return res.redirect("/register");
  }

  const passwordPattern = /^[^\s]{8,50}$/;
  if (!passwordPattern.test(password)) {
    req.session.passwordErrorMessage = "Пароль должен иметь длину от 8 до 50 символов";

    return res.redirect("/register");
  }

  try {
    const emailCheck = await pool.query(
      `SELECT * FROM ganiev.users WHERE email = $1`,
      [email]
    );

    if (emailCheck.rows.length > 0) {
      req.session.emailErrorMessage = "Такой адрес уже занят";

      return res.redirect("/register");
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    const insertUserQuery = `
      INSERT INTO ganiev.users (username, email, password) 
      VALUES ($1, $2, $3) RETURNING user_id
    `;
    await pool.query(insertUserQuery, [
      username,
      email,
      hashedPassword,
    ]);

    req.session.emailErrorMessage = "";
    res.redirect("/login");
  } catch (error) {
    console.error("Ошибка регистрации:\n", error);
    res.sendStatus(500);
  }
});

app.post("/cancelReservation", async (req, res) => {
  const { tableNumber, date, time } = req.body;

  try {
    await pool.query(
      `DELETE FROM ganiev.reserved_tables 
      WHERE table_id = $1 
      AND   date = $2 
      AND   time = $3`,
      [tableNumber, date, time]
    );

    res.redirect("/profile");
  } catch (error) {
    console.error("Ошибка отмены столика:\n", error);
    res.sendStatus(500);
  }
});

app.get("/logout", (req, res) => {
  req.session.destroy(err => {
    if (err) {
      console.error("Ошибка при выходе из системы:", err);
      return res.sendStatus(500);
    }
    res.clearCookie('connect.sid'); // Удаление куки сессии
    res.redirect("/login");
  });
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
