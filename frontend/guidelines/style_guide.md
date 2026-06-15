# Qdra Design Philosophy & Frontend Style Guide

## Purpose

This document defines the visual identity of Qdra.

It exists to ensure that all AI-generated frontend work follows a consistent design language.

This guide should be provided to any coding agent implementing frontend features.

The goal is not visual creativity.

The goal is consistency.

---

# Design Philosophy

Qdra is not:

- A marketing website
- A social network
- A mobile-first application
- A colorful dashboard
- A traditional enterprise CRUD application

Qdra is:

- A technical workspace
- A planning tool
- A graph exploration tool
- A knowledge system
- A tool for power users

The interface should feel like:

- Obsidian
- Linear
- Notion
- Modern developer tools

The UI should communicate:

- Clarity
- Focus
- Structure
- Calmness
- Technical depth

---

# Core Principles

## 1. Everything Important Is A Card

Cards are the primary building block of the application.

Avoid large flat pages.

Avoid giant forms.

Avoid endless tables.

Whenever possible:

- Projects are cards
- Materials are cards
- Recipes are cards
- Planning runs are cards
- Settings sections are cards

---

## 2. The Background Disappears

The page background exists only to make cards stand out.

Background should be nearly black.

Example:

```css
background: #080808;
```

The user should focus on the cards, not the page.

---

## 3. Information Is Grouped

Large forms should be split into logical cards.

Bad:

```text
One giant form with 30 fields
```

Good:

```text
Material

[Identity Card]

[Parameters Card]

[Relationships Card]
```

---

## 4. Visual Hierarchy Through Size

Use size and spacing before using color.

Prefer:

- Bigger titles
- Better spacing
- Clear grouping

Instead of:

- Bright colors
- Heavy borders
- Excessive visual effects

---

## 5. One Accent Color

Use a single accent color.

The accent exists to show:

- Selection
- Navigation state
- Primary actions

The accent does not exist for decoration.

---

## 6. Calm UI

Avoid:

- Animations everywhere
- Bright colors
- Aggressive shadows
- Huge gradients

Qdra should feel calm and deliberate.

---

# Color System

## Background

```css
--bg-main: #080808;
--bg-secondary: #101010;
```

## Card Surface

```css
--card-bg: rgba(255,255,255,0.05);
--card-bg-hover: rgba(255,255,255,0.08);
```

## Borders

```css
--border: rgba(255,255,255,0.08);
--border-hover: rgba(255,255,255,0.14);
```

## Text

```css
--text-primary: #f5f5f5;
--text-secondary: #cfcfcf;
--text-muted: #8c8c8c;
```

## Accent

```css
--accent: #60A5FA;
--accent-hover: #3B82F6;
```

## Status

```css
--success: #22C55E;
--warning: #EAB308;
--danger: #EF4444;
```

---

# Card Style

Cards are the heart of the application.

```css
background: var(--card-bg);
border: 1px solid var(--border);
border-radius: 18px;

box-shadow:
  0 4px 12px rgba(0,0,0,0.25),
  0 12px 32px rgba(0,0,0,0.20);

backdrop-filter: blur(8px);
```

Cards should feel like floating panels.

Not heavy.

Not glassmorphism.

Just slightly elevated.

---

# Corner Radius

Use generous rounded corners.

```css
--radius-small: 12px;
--radius-medium: 18px;
--radius-large: 24px;
```

Avoid sharp corners.

Avoid tiny radii.

---

# Shadows

Shadows should be subtle.

Good:

```css
box-shadow:
  0 4px 12px rgba(0,0,0,0.25);
```

Bad:

```css
Huge glowing shadows
```

The user should barely notice the shadow.

---

# Layout

## Page Structure

```text
Header

Page Content
```

Keep layouts simple.

---

## Content Width

Forms:

```text
600px - 900px
```

Catalogs:

```text
Full width
```

---

# Project Catalog Layout

Projects should be displayed as cards.

Not tables.

Example:

```text
┌────────────────────┐
│ Satisfactory       │
│ Factory planning   │
│                    │
│ Open     Edit      │
└────────────────────┘
```

Layout:

```css
display: grid;
grid-template-columns:
repeat(auto-fill, minmax(320px, 1fr));
```

---

# Material Catalog Layout

Materials should use horizontal cards.

Example:

```text
┌─────────────────────────────────┐
│ Iron Ore                        │
│ Resource                        │
│                     Edit  Open  │
└─────────────────────────────────┘
```

Compact and information-dense.

---

# Recipe Catalog Layout

Recipes should use richer cards.

Example:

```text
┌───────────────────────────────┐
│ Iron Plate                    │
│ Inputs: 1                     │
│ Outputs: 1                    │
│                               │
│ Edit                    Open  │
└───────────────────────────────┘
```

---

# Forms

Forms should be card-based.

Example:

```text
Material

┌───────────────────┐
│ Identity          │
│ Name              │
└───────────────────┘

┌───────────────────┐
│ Parameters        │
│ Category          │
│ Purity            │
└───────────────────┘
```

Never create giant forms.

---

# Buttons

## Primary

Filled accent color.

Used for:

- Create
- Save
- Run Planning

## Secondary

Transparent with border.

Used for:

- Cancel
- Edit
- Back

## Danger

Red.

Only for destructive actions.

---

# Typography

Font:

```css
Inter, system-ui, sans-serif
```

Page title:

```css
32px
700
```

Section title:

```css
20px
600
```

Body:

```css
14px
```

Avoid oversized typography.

---

# Empty States

Every catalog must have an empty state.

Example:

```text
No projects found.

Create your first project.

[Create Project]
```

Never show a blank page.

---

# Loading States

Prefer simple loading text.

Example:

```text
Loading projects...
Loading materials...
Running planning...
```

Simple is better than elaborate spinners.

---

# Navigation

Future project workspace layout:

```text
┌─────────────────────────────┐
│ Qdra > Satisfactory         │
└─────────────────────────────┘

┌────────────┐ ┌──────────────┐
│ Sidebar    │ │ Content      │
│            │ │              │
└────────────┘ └──────────────┘
```

Sidebar should also use card styling.

---

# What To Avoid

Do not generate:

- White backgrounds
- Browser default forms
- Browser default tables
- Tiny cards
- Sharp corners
- Rainbow colors
- Huge gradients
- Dashboard widgets everywhere
- Marketing website layouts
- Centered landing-page style content

---

# AI Implementation Rule

When implementing a screen:

1. Start with a dark background.
2. Place content inside cards.
3. Use rounded corners.
4. Use subtle shadows.
5. Use a single accent color.
6. Prefer grids over tables.
7. Split information into multiple cards.
8. Keep visual noise low.
9. Optimize for readability.
10. Make the UI feel like a workspace, not a website.
