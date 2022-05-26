function encodeText(text, no_behind = 7) {
  let array = [];
  let buffer = new Buffer(text);
  let result = buffer.forEach((i, index) => array.push(buffer[index]));
  let transform = Buffer.from(array.map(x => x + 7));
  return transform.toString("base64");
}

function decodeText(text, no_behind = 7) {
  let result = Buffer.from(text, "base64").toString("ascii");
  console.log(result);
  let array = [];
  let buffer = new Buffer(result);
  let transform = buffer.forEach((i, index) =>
    array.push(buffer[index] - no_behind)
  );
  return Buffer.from(array).toString();
}

function getDomain() {
  return [
    {
      index: "01",
      domain: "http://localhost:3000"
    },
    {
      index: "02",
      domain: "https://staging.careerlyft.com"
    },
    {
      index: "03",
      domain: "https://app.careerlyft.com"
    }
  ];
}

class Application {
  encode(text, no_behind = 7, expires, domain = "") {
    let fullText = text;
    if (expires) {
      fullText = `${fullText}-ed:${expires}`;
    }
    let result = encodeText(fullText);
    result += `-d:${domain}`;
    return encodeURIComponent(result);
  }
  decode(code) {
    let withoutDomain = decodeURIComponent(code).split("-d:");
    let domain = undefined;
    if (withoutDomain.length > 1) {
      domain = withoutDomain[1] || undefined;
    }
    let decoded = decodeText(withoutDomain[0]);
    let dateSplit = decoded.split("-ed:");
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
      instance = getDomain().find(x => x.index === domain);
      if (instance) {
        domain = instance.domain;
      }
    }
    let result = {
      text: splitBySalt,
      expires,
      expired,
      domain
    };
    return result;
  }
  generateUrl(result, path = "") {
    if (!result.expired && result.domain) {
      let constructedString = `${result.domain}{path}`;
      if (result.expires) {
        let asTimestamp = new Date(result.expires).getTime();
        constructedString += `${asTimestamp}/`;
      }
      return `${constructedString}${result.text}`;
    }
  }
}

module.exports = Application;
