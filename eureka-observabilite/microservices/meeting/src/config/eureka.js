const Eureka = require('eureka-js-client').Eureka;

/**
 * Enregistre Meeting dans Eureka avec les URL de sante et d'info.
 * Variables d'environnement : PORT, EUREKA_HOST, EUREKA_PORT, HOST_NAME
 */
function startEurekaClient(port) {
  const hostName = process.env.HOST_NAME || 'localhost';
  const baseUrl = `http://${hostName}:${port}`;

  const client = new Eureka({
    instance: {
      app: 'MEETING',
      // instanceId unique par instance (utile quand on lance plusieurs ports)
      instanceId: `${hostName}:meeting:${port}`,
      hostName,
      ipAddr: '127.0.0.1',
      port: { $: Number(port), '@enabled': true },
      vipAddress: 'meeting',
      statusPageUrl: `${baseUrl}/info`,
      healthCheckUrl: `${baseUrl}/health`,
      homePageUrl: `${baseUrl}/`,
      dataCenterInfo: {
        '@class': 'com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo',
        name: 'MyOwn',
      },
    },
    eureka: {
      host: process.env.EUREKA_HOST || 'localhost',
      port: Number(process.env.EUREKA_PORT || 8761),
      servicePath: '/eureka/apps/',
    },
  });

  client.logger.level('info');
  client.start((error) => {
    console.log(error ? `Eureka: echec de l'enregistrement (${error})` : 'Eureka: MEETING enregistre');
  });

  // Se desenregistrer proprement a l'arret
  const stop = () => client.stop(() => process.exit(0));
  process.on('SIGINT', stop);
  process.on('SIGTERM', stop);
  return client;
}

module.exports = startEurekaClient;
