const { createServer } = require('http');

function encodeText(text, no_behind = 7) {
  let array = [];
  let buffer = new Buffer(text);
  let result = buffer.forEach((i, index) => array.push(buffer[index]));
  let transform = Buffer.from(array.map(x => x + 7));
  let result2 = transform.toString('base64');
  return result2;
}

function decodeText(text, no_behind = 7) {
  // let result = Buffer.from(text, "base64").toString("ascii");
  // let result = Buffer.from(text, "base64").toString("utf-8");
  let result = Buffer.from(text, 'base64');
  console.log(result);
  let array = [];
  let buffer = result;
  // let buffer = new Buffer(result);
  let transform = buffer.forEach((i, index) =>
    array.push(buffer[index] - no_behind)
  );
  let rr = Buffer.from(array).toString();
  return rr;
}

function getDomain() {
  return [
    {
      index: '01',
      domain: 'http://localhost:3000',
    },
    {
      index: '02',
      domain: 'https://agent-staging.careerlyft.com',
    },
    {
      index: '03',
      domain: 'https://agent.careerlyft.com',
    },
  ];
}

class Application {
  encode(text, expires, domain = '') {
    let fullText = text;
    if (expires) {
      fullText = `${fullText}-ed:${expires}`;
    }
    let result = encodeText(fullText);
    result += `-d:${domain}`;
    return encodeURIComponent(result);
  }
  decode(code) {
    let withoutDomain = decodeURIComponent(code).split('-d:');
    let domain = undefined;
    if (withoutDomain.length > 1) {
      domain = withoutDomain[1] || undefined;
    }
    let decoded = decodeText(withoutDomain[0]);
    let dateSplit = decoded.split('-ed:');
    let splitBySalt = dateSplit[0];
    let expires = undefined;
    let expired = false;
    if (dateSplit.length > 1) {
      expires = dateSplit[1];
      try {
        let asDAte = new Date(expires);
        expired = Date.now() > asDAte.getTime();
      } catch (e) {}
    }
    if (domain) {
      let instance = getDomain().find(x => x.index === domain);
      if (instance) {
        domain = instance.domain;
      }
    }
    let result = {
      text: splitBySalt,
      expires,
      expired,
      domain,
    };
    return result;
  }
  generateUrl(result, path = '') {
    if (!result.expired && result.domain) {
      let constructedString = `${result.domain}${path}`;
      if (result.expires) {
        let asTimestamp = new Date(result.expires).getTime();
        constructedString += `${asTimestamp}/`;
      }
      return `${constructedString}${result.text}`;
    }
  }
}

const PORT = process.env.PORT || 8080;

function homeRoute(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'Origin, X-Requested-With, Content-Type, Accept'
  );
  res.setHeader(
    'Access-Control-Allow-Methods',
    'GET, POST, PATCH, DELETE, OPTIONS'
  );
  if (req.method === 'GET') {
    res.setHeader('Content-Type', 'application/json');
    res.statusCode = 200;
    res.end(JSON.stringify({ hello: 'world' }));
  } else {
    if (req.method === 'POST') {
      let data = '';
      req.on('data', chunk => {
        data += chunk;
      });
      req.on('end', () => {
        try {
          const requestData = JSON.parse(data);
          let appInstance = new Application();
          let baseUrl = req.headers['host'];
          console.log(req.headers);
          let result = appInstance.encode(
            requestData.text,
            requestData.expires,
            requestData.domain || ''
          );
          if (requestData.domain) {
            res.setHeader('Content-Type', 'application/json');
            res.statusCode = 200;
            res.end(JSON.stringify({ url: `${baseUrl}/${result}` }));
          } else {
            res.setHeader('Content-Type', 'application/json');
            res.statusCode = 200;
            res.end(JSON.stringify({ data: result }));
          }
        } catch (e) {
          console.log(e);
          res.statusCode = 400;
          res.end('Invalid JSON');
        }
      });
    }
  }
}
function secondaryRoute(req, res) {
  if (req.method === 'GET') {
    let encodedString = req.url.slice(1);
    let appInstance = new Application();
    let result = appInstance.decode(encodedString);
    console.log(result);
    if (result.domain) {
      let url = appInstance.generateUrl(result, '/edit-resumes/');
      res.setHeader('Location', url);
      res.statusCode = 302;
      res.end();
    } else {
      res.setHeader('Content-Type', 'application/json');
      res.statusCode = 200;
      res.end(JSON.stringify(result));
    }
  } else {
    res.end();
  }
}
const server = createServer((req, res) => {
  if (req.url === '/') {
    homeRoute(req, res);
  } else {
    secondaryRoute(req, res);
  }
});

server.listen(PORT, () => {
  console.log(`starting server at port ${PORT}`);
});
