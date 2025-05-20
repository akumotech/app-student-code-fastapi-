# Student Dashboard API Documentation

This document describes the backend API endpoints for managing student certificates and demos. These endpoints are designed for easy expansion to support future features such as classes, curriculum, interviews, and events.

---

## Table of Contents

- [Overview](#overview)
- [Certificates](#certificates)
  - [List Certificates](#list-certificates)
  - [Create Certificate](#create-certificate)
  - [Update Certificate](#update-certificate)
  - [Delete Certificate](#delete-certificate)
- [Demos](#demos)
  - [List Demos](#list-demos)
  - [Create Demo](#create-demo)
  - [Update Demo](#update-demo)
  - [Delete Demo](#delete-demo)
- [Authentication & Permissions](#authentication--permissions)
- [Scalability & Future Features](#scalability--future-features)

---

## Overview

The Student Dashboard API allows students to manage their certificates and demos. Each student can:

- View, add, update, and delete their certificates
- View, add, update, and delete their demos

All endpoints are protected and require authentication.

---

## Certificates

### List Certificates

- **Endpoint:** `GET /students/{student_id}/certificates`
- **Description:** Retrieve all certificates for a student.
- **Response Example:**

```json
[
  {
    "id": 1,
    "name": "Python Basics",
    "issuer": "Coursera",
    "date_issued": "2024-01-01",
    "description": "Introductory Python course."
  }
]
```

### Create Certificate

- **Endpoint:** `POST /students/{student_id}/certificates`
- **Description:** Add a new certificate for a student.
- **Request Example:**

```json
{
  "name": "Python Basics",
  "issuer": "Coursera",
  "date_issued": "2024-01-01",
  "description": "Introductory Python course."
}
```

### Update Certificate

- **Endpoint:** `PUT /students/{student_id}/certificates/{certificate_id}`
- **Description:** Update an existing certificate.
- **Request Example:**

```json
{
  "name": "Advanced Python",
  "issuer": "Coursera",
  "date_issued": "2024-02-01",
  "description": "Advanced Python course."
}
```

### Delete Certificate

- **Endpoint:** `DELETE /students/{student_id}/certificates/{certificate_id}`
- **Description:** Remove a certificate from a student.

---

## Demos

### List Demos

- **Endpoint:** `GET /students/{student_id}/demos`
- **Description:** Retrieve all demos for a student.
- **Response Example:**

```json
[
  {
    "id": 1,
    "title": "Portfolio Website",
    "description": "Personal portfolio built with React.",
    "link": "https://myportfolio.com",
    "date": "2024-03-01"
  }
]
```

### Create Demo

- **Endpoint:** `POST /students/{student_id}/demos`
- **Description:** Add a new demo for a student.
- **Request Example:**

```json
{
  "title": "Portfolio Website",
  "description": "Personal portfolio built with React.",
  "link": "https://myportfolio.com",
  "date": "2024-03-01"
}
```

### Update Demo

- **Endpoint:** `PUT /students/{student_id}/demos/{demo_id}`
- **Description:** Update an existing demo.
- **Request Example:**

```json
{
  "title": "Updated Portfolio Website",
  "description": "Updated with new projects.",
  "link": "https://myportfolio.com",
  "date": "2024-04-01"
}
```

### Delete Demo

- **Endpoint:** `DELETE /students/{student_id}/demos/{demo_id}`
- **Description:** Remove a demo from a student.

---

## Authentication & Permissions

- All endpoints require authentication.
- Students can only manage their own certificates and demos.
- Admins may have access to manage all students' data (future feature).

---

## Scalability & Future Features

- The API structure allows for easy addition of new features such as classes, curriculum, interviews, and events.
- New endpoints can be added under `/students/{student_id}/` as needed.
- Data models are designed to be extensible for future requirements.

---

For questions or suggestions, contact the backend development team.
