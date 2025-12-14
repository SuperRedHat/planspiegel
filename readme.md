# Project Deployment Information

This project has successfully implemented CI/CD pipelines for both the frontend and backend components. Below are the details:

## Deployment Status

- **Frontend**: CI/CD deployment completed.
- **Backend**: CI/CD deployment completed.

## Frontend Access

The homepage of the frontend can be accessed at the following URL:
**[https://planspiegel.com](https://planspiegel.com)** 
or
**[https://134.109.116.232](https://134.109.116.232)**

> **Note:** This URL is accessible only within the campus network or when connected to the campus VPN. 
>
>Because --manual mode is used, the certificate will not be renewed automatically. Before the certificate expires (for example, 30 days before expiration), you need to repeat the following command to renew it:
>```bash
>sudo certbot certonly --manual --preferred-challenges dns -d planspiegel.com -d www.planspiegel.com
>```

## Backend Access

The backend API and services have been deployed alongside the frontend. For detailed API endpoints and usage, refer to the API documentation within the project.

## Notes

1. Ensure that you have the necessary permissions or VPN access to connect to the campus network for accessing the frontend.
2. For any issues with deployment or access, please contact the project maintainer.

---