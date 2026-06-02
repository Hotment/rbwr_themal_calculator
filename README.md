# ⚡ RBWR APR Transparent Overlay Calculator

A sleek, modern, zero-dependency Python desktop overlay designed for the Roblox **Realistic Boiling Water Reactor (RBWR)** simulation. This utility allows you to instantly calculate Reactor Thermal Power (RTP% / APRM) and other essential values from MWt demand (and vice-versa) directly on your screen while playing!

Inspired by and numerically identical to the calculations at [rbwr.nxrvi.com/tools/demandcalc.html](https://rbwr.nxrvi.com/tools/demandcalc.html).

---

## ✨ Features

- 🖥️ **Always-On-Top Overlay**: Stays pinned on top of your Roblox game window.
- 🪟 **Glassmorphic Transparency**: Dynamic transparency slider (from 30% to 100% opacity) for optimal visibility.
- 🖱️ **Borderless & Draggable**: Click and drag anywhere on the panel to reposition it seamlessly.
- ⚡ **Bidirectional Live Calculations**:
  - Enter **MWt (Demand)** to get **RTP (%)**, **Gen Load (MWe)**, and **Feedwater Flow (kg/s)**.
  - Enter **RTP (%)** to get the required **MWt (Demand)**, **Gen Load (MWe)**, and **Feedwater Flow (kg/s)**.
- 🎛️ **Dual-Unit Support**: Quick toggle tabs for both **Unit 1** and **Unit 2** calculations.
- ⚙️ **Configurable Site Usage**: Adjust the **Site Usage in MWe** (default: `61.32`) to fit your current reactor setup.
- 🔢 **Demand Quick Steps**: `-10` / `+10` quick adjust buttons to easily step your load in multiples of 10.
- 🚨 **Overpower Warning**: Instantly activates a crimson isotope-glow warning screen if the calculated thermal power goes above the safe limit (**110% RTP for Unit 1**, and **115% RTP for Unit 2**).
- ⛶ **Ultra-Compact Mode**: Collapses the overlay into a tiny, space-saving bar (`360x60` px) displaying only essential parameters: `[Unit] [Input MWt] ➔ [RTP%] [Feedwater]`.

---

## 🚀 How to Run

Since the application is written in standard Python using `tkinter`, it has **zero external dependencies**! You do not need to install anything.

1. Open your terminal or Command Prompt in the workspace directory.
2. Run the application:
   ```bash
   python rbwr_overlay.py
   ```

---

## 🎮 Overlay Controls

- **Reposition Window**: Left-click and hold anywhere on the title bar or background card, then drag your mouse.
- **Toggle Always-on-Top**: Click the pin icon (`📌` / `📍`) on the top right.
- **Toggle Compact Mode**: Click the window icon (`⛶`) to shrink the UI to a tiny in-game HUD. Click it again to expand to detailed view.
- **Step Demand +/- 10**: Click the `-10` / `+10` buttons next to the demand input in detailed mode, or click `-` / `+` next to it in compact mode to instantly step the demand.
- **Toggle Unit**: Click the **UNIT 1** / **UNIT 2** tabs in detailed mode, or click the **U1** / **U2** badge in compact mode.
- **Close Utility**: Click the `✕` in the top right.

---

## 📊 Math & Formulas Reference

### Unit 1
*   **Thermal Power (%)** from Demand ($d$):
    $$Thermal = \max\left(0, \frac{-13 + \sqrt{169 + 0.02132 \times (d + 135 + siteUsage)}}{0.01066}\right)$$
*   **Gen Load (MWe)**:
    $$GenLoad = \max\left(0, -135 + 13 \times t + 5.33 \times 10^{-3} \times t^2\right)$$
*   **Feedwater Flow (kg/s)**:
    $$Flow = \max\left(0, 82.8 + 13.7 \times t + 5.87 \times 10^{-3} \times t^2\right) + 2$$

### Unit 2
*   **Thermal Power (%)** from Demand ($d$):
    $$Thermal = \max\left(0, \frac{-12.5 + \sqrt{156.25 + 0.00824 \times (d + 143 + siteUsage)}}{0.00412}\right)$$
*   **Gen Load (MWe)**:
    $$GenLoad = \max\left(0, -143 + 12.5 \times t - 2.06 \times 10^{-3} \times t^2\right)$$
*   **Feedwater Flow (kg/s)**:
    $$Flow = \max\left(0, 115 + 12.2 \times t + 9.27 \times 10^{-3} \times t^2\right) + 2$$
