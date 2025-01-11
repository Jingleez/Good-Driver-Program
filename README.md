# Good Driver Incentive Program

## Project Overview

This project was developed as a group project for **CPSC 4910**.

The **Good (Truck) Driver Incentive Program** is a web application designed to improve on-road performance among truck drivers by implementing an incentive-based reward system. Sponsors (companies) can reward drivers with points for good driving behavior, which can then be redeemed for products from a sponsor-specific catalog. The application provides comprehensive functionality for drivers, sponsors, and admin users, leveraging modern web technologies and third-party APIs for a robust and scalable solution.

---

## Features

### **Drivers**
- **Point Rewards**: Earn points for safe and efficient driving practices.
- **Catalog Browsing**: Browse products available in the sponsor’s catalog.
- **Product Redemption**: Redeem points for catalog products.
- **Profile Management**: Update user profile and password.
- **Purchase Management**: Review and manage purchases.

### **Sponsors**
- **Driver Applications**: Review and approve/reject driver applications.
- **Point Management**: Add or deduct points for drivers, with reasons logged.
- **Catalog Management**: Maintain a custom product catalog using a public API.
- **Reports**: Generate reports on driver points and audit logs.
- **Driver Assistance**: Purchase products on behalf of drivers.
- **Role Management**: Create and manage sponsor users.

### **Admins**
- **User Management**: Review and update any driver, sponsor, or admin profile.
- **System Management**: Add new users (drivers, sponsors, and admins).
- **Audit Logs**: Generate detailed logs for significant state changes.
- **Reports**: Generate sales and audit reports for sponsors and drivers.

---

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript (with responsive design).
- **Backend**: Flask (Python) for API and server-side logic.
- **Database**: MySQL (hosted on AWS RDS) for storing user, catalog, and transaction data.
- **Third-Party APIs**: eBay/iTunes/Overstock/ETSY for real-time product catalog integration.
- **Hosting**: AWS EC2 instance for application deployment.

---

## Key Features

### **Security**
- Enforced password complexity.
- Encryption of user passwords and private information at rest.
- Protection against SQL injection attacks.
- Secure password reset functionality.

### **Reports**
#### Sponsor Reports:
- Track driver points by date range and category.
- Audit logs restricted to sponsor-affiliated drivers.

#### Admin Reports:
- Sales by sponsor or driver.
- Detailed invoice summaries.
- Audit logs by date range and category.

---

## License

This project was developed as part of an academic requirement and is intended for educational purposes only.
