const express = require("express");
const { Client } = require("pg");
const dbConfig = require('./dbConfig');
const helmet = require("helmet"); 
const session = require("express-session");
const app = express();
const PORT = 3000;
const PEOPLE_AMOUNT = 5;
const TABLE_AMOUNT = 10;

app.set("view-engine", "ejs");
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
app.use(express.static(`${__dirname}`));
app.use(express.urlencoded({ extended: false }));
app.use(
  session({
    secret: "mySecret",
    resave: true,
    saveUninitialized: false,
    cookie: { maxAge: 3600000 },
  })
);

const client = new Client(dbConfig);

client
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
    const userResult = await client.query(
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

    if (typeof userResult.rows === 'undefined') {
      return res.redirect("/login");
    }

    const allUserReservations = [];
    for (let i = 0; i < userResult.rows.length; ++i) {
      const peopleCount = userResult.rows[i].people_count;
      const tableNumber = userResult.rows[i].table_id;
      const date        = userResult.rows[i].formatted_date;
      const time        = userResult.rows[i].formatted_time;

      allUserReservations.push({peopleCount, tableNumber, date, time});
    }
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
  const formattedDate = new Date().toISOString().split('T')[0]; // Формат YYYY-MM-DD
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

  const datePattern = /^20[0-9]{2}-[0-9]{2}-[0-9]{2}$/;
  if (!datePattern.test(date) || (new Date(date) < new Date().setHours(18, 0, 0, 0))) {
    req.session.reservationErrorMessage = "Некорректная дата бронирования";

    return res.redirect("/reservation");
  }

  const timePattern = /^[0-9]{2}:[0-9]{2}$/;
  const hours       = parseInt(time.split(":")[0]);
  const minutes     = parseInt(time.split(":")[1]);
  if (!timePattern.test(time) || (hours < 18 && hours >= 6) || minutes < 0 || minutes > 59) {
    req.session.reservationErrorMessage = "Некорректное время бронирования";

    return res.redirect("/reservation");
  }

  try {
    const reservationCheck = await client.query(
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
    const result = await client.query(insertReservationQuery, [
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
    const userResult = await client.query(
      `SELECT * FROM ganiev.users WHERE email = $1`,
      [email]
    );

    const user = userResult.rows[0];
    if (!user) {
      req.session.emailErrorMessage = "Несуществующий email";

      return res.redirect("/login");
    }

    if (password === user.password) {
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
    const emailCheck = await client.query(
      `SELECT * FROM ganiev.users WHERE email = $1`,
      [email]
    );

    if (emailCheck.rows.length > 0) {
      req.session.emailErrorMessage = "Существующий email";

      return res.redirect("/register");
    }

    const insertUserQuery = `
      INSERT INTO ganiev.users (username, email, password) 
      VALUES ($1, $2, $3) RETURNING user_id
    `;
    const result = await client.query(insertUserQuery, [
      username,
      email,
      password,
    ]);

    req.session.emailErrorMessage = "";
    res.redirect("/login");
  } catch (error) {
    console.error("Ошибка регистрации:\n", error);
    res.sendStatus(500);
  }
});

app.get("/logout", (req, res) => {
  req.session.destroy();
  res.redirect("/profile");
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});

app.post("/cancelReservation", async (req, res) => {
  const { tableNumber, date, time } = req.body;

  try {
    await client.query(
      `DELETE FROM ganiev.reserved_tables 
      WHERE table_id = $1 
        AND date = $2 
        AND time = $3`,
      [tableNumber, date, time]
    );

    res.redirect("/profile");
  } catch (error) {
    console.error("Ошибка отмены столика:\n", error);
    res.sendStatus(500);
  }
});
