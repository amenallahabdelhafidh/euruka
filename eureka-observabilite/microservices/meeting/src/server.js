const app = require('./app');
const startEurekaClient = require('./config/eureka');

const PORT = process.env.PORT || 8083;

app.listen(PORT, () => {
  console.log(`meeting microservice running on http://localhost:${PORT}`);
  console.log(`Swagger UI: http://localhost:${PORT}/swagger-ui`);
  console.log(`Health: http://localhost:${PORT}/health | Info: http://localhost:${PORT}/info`);

  // EUREKA_ENABLED=false pour desactiver l'enregistrement
  if (process.env.EUREKA_ENABLED !== 'false') {
    startEurekaClient(PORT);
  }
});
