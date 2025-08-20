# User Guide (Detailed Overview)
[![Русский](https://img.shields.io/badge/lang-Русский-blue.svg)](../ru/user_guide.md)

This document is your guide to the Bomberman Online web interface. Here you will find a detailed description of all features: from creating an account and logging into the game to advanced capabilities like the map editor and game session management.

## 1. Authentication and Account Management

An account is required to access most features.

### 1.1. Registration (`/account/register`)

1.  **Go to the page:** Click the "Register" button on the main page.
2.  **Fill out the form:** You will be presented with a form containing the following fields:
    *   **Username:** Your unique in-game nickname (from 3 to 30 characters). This field is required.
    *   **Email:** Your valid email address. Used for login, verification, and password recovery. This field is required.
    *   **Full Name (optional):** Your real name. This field is optional.
    *   **Password:** A strong password (minimum 8 characters). This field is required.
    *   **Confirm Password:** Repeat the password. This field must match the "Password" field.
3.  **Submit:** After clicking the "Register" button, the system will validate the data. If successful, your account will be created, and you will see a message asking you to check your email to complete the registration.

### 1.2. Email Verification (`/account/verify-email`)

After registration, you need to confirm your email.

1.  **Check your email:** Find the email from Bomberman Online in your inbox.
2.  **Click the link:** The email will contain a unique link. Click on it.
3.  **Completion:** You will be redirected to a confirmation page where you will see a message about the successful activation of your account. You can now log into the game.

### 1.3. Login (`/account/login`)

1.  **Go to the page:** Click the "Login" button.
2.  **Enter credentials:** Enter your **username** and password.
3.  **Remember me:** If you want the system to remember you, check this box. Your session will be saved in `localStorage`.
4.  **Login:** Click the "Login" button. Upon successful authorization, you will be redirected to your dashboard (`/account/dashboard`). In case of an error (incorrect password or username), you will see a corresponding notification.

### 1.4. Password Reset (`/account/reset-password`)

1.  **Request a reset:** On the login page, click the "Forgot password?" link.
2.  **Enter Email:** Provide the email you used during registration.
3.  **Check your email:** You will receive an email with a link to a page for creating a new password.
4.  **Create a new password (`/account/confirm-reset-password`):** Follow the link from the email. Enter a new password and confirm it. After saving, you will be able to log in with the new password.

## 2. Dashboard (`/account/dashboard`)

This is your home page after logging in.

*   **Profile Card:** Displays your avatar, username, email, and role. There is a button to go to the profile editing page.
*   **Gaming Features:** A set of cards for quick access to the main functions:
    *   **Start Game:** Redirects to the new game creation page (`/account/games/create`).
    *   **Game List:** Navigates to the list of all available game rooms (`/account/games`).
    *   **Map Editor:** Navigates to the powerful map editor (`/account/maps/editor`).
    *   **Statistics:** Navigates to the page with your game statistics (`/account/stats`).

## 3. Gameplay

### 3.1. Creating a Game (`/account/games/create`)

1.  **Settings:**
    *   **Game Mode:** A dropdown list to select the mode (e.g., `Campaign`, `Free For All`).
    *   **Max Players:** A numeric field to specify the player limit (from 2 to 8).
    *   **Map Template (optional):** A dropdown list with all maps created in the editor. If not selected, the default map will be used.
2.  **Create:** Clicking the "Create Game" button sends a request to the `WebAPI Service` and, if successful, redirects you to the game screen (`/account/game/:gameId`).

### 3.2. Game Screen (`/account/game/:gameId`)

This is the main window where all the gameplay happens.

*   **Game Field (`GameCanvas`):** The central part of the screen where the game is rendered in real-time.
*   **Smooth Camera:** The camera smoothly follows your character, starting to move only when the character goes beyond the central "dead zone."
*   **Information Panel (at the top):** Displays the game ID, level, and status (Waiting, Active, Paused, Finished).
*   **Controls Hint:** A reminder is always displayed below the game field: "Use WASD or arrow keys to move, spacebar to place a bomb."

### 3.3. Controls and Hotkeys

Controls are implemented in `src/services/InputHandler.ts`.

| Key(s) | Action |
| :--- | :--- |
| **`W`** / **`↑`** (Up Arrow) | Move Up |
| **`S`** / **`↓`** (Down Arrow) | Move Down |
| **`A`** / **`←`** (Left Arrow) | Move Left |
| **`D`** / **`→`** (Right Arrow) | Move Right |
| **`Spacebar`** | Place primary weapon (bomb) |
| **`R`** | Restart game (if available) |

## 4. Game Management (`/account/games/:gameId/manage`)

This is not a separate page, but a modal window that opens over the game screen when you click the gear icon in the header.

### 4.1. Your Participation in the Game

*   **If you are not in the game:**
    *   You can choose a **unit type** (`Bomberman` or `Tank`).
    *   Click the **"Join Game"** button.
*   **If you are already in the game:**
    *   You see your current unit type.
    *   You can **change your unit type** (this will recreate your character in the lobby).
    *   You can click **"Leave Game"**.

### 4.2. General Information and Actions

*   **Information:** Displays status, mode, number of players, level, etc.
*   **Map Selection:** You can change the map template for the game if it has not started yet.
*   **Game Actions:**
    *   **Start Game:** Available if there is at least one player in the lobby.
    *   **Pause/Resume Game:** Controls the pause during a match.
    *   **Delete Game:** Completely deletes the session.

### 4.3. Player and Team Management

*   **Player List:** Displays all players in the lobby, their status, lives, and coordinates.
*   **Add Player:** An administrator can manually add a player by their ID.
*   **Remove Player:** An administrator can kick a player from the lobby.
*   **Team Management (for `Capture The Flag` mode):**
    *   Create and delete teams.
    *   Automatic player distribution.
    *   Manual movement of players between teams.

## 5. Map Editor (`/account/maps/editor`)

A powerful tool for creating and managing game maps.

### 5.1. Map Templates

*   **Creation:**
    1.  Click "Create new map template".
    2.  In the dialog box, set the **name, description, dimensions (width/height), difficulty (1-10), and max players (1-8)**.
    3.  **Interactive Editor:**
        *   **Palette:** Select the cell type for drawing (`Solid Wall`, `Destructible Block`, `Player Spawn`, etc.).
        *   **Grid:** Hold down the left mouse button and drag across the grid to "draw" with the selected block type.
    4.  Click "Create" to save the map.
*   **Management:** Existing templates can be viewed, edited (the same editor will open with the data pre-filled), or deleted.

### 5.2. Map Groups and Chains

*   **Map Groups:** Allow you to group maps by a certain characteristic (e.g., "Winter Maps," "Duel Maps").
*   **Map Chains:** Allow you to create sequences of maps for the campaign mode. When creating a chain, you select several templates from the list, and they will be loaded in the specified order as you progress.

## 6. Profile and Statistics

### 6.1. Profile (`/account/profile`)

*   **View:** Displays your avatar, username, registration date, email, and verification status.
*   **Edit:** You can change your **username**, **full name**, and **avatar URL**.

### 6.2. Statistics (`/account/stats`)

This page (currently with demo data) will display your detailed game statistics, including the number of wins, losses, win rate, total score, and other game achievements.