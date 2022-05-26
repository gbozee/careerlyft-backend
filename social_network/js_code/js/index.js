import React from "react";
import { render } from "react-dom";
import Hello from "./Hello";
import hello from "hellojs";

const LINKEDIN_CLIENT_ID = "86dpi58dscrfi0";
hello.init(
	{
		linkedin: LINKEDIN_CLIENT_ID
	},
	{
		// scope: ["friends", "email"],
		get: {
			me:
				"people/~:(picture-url,first-name,headline,last-name,id,location,email-address)",

			// See: http://developer.linkedin.com/documents/get-network-updates-and-statistics-api
			"me/share": "people/~/network/updates?count=@{limit|250}"
		},

		redirect_uri:
			"http://localhost:1234/dist/faf1791ce74daee66ab43ca4d12c5840.html",
		oauth_proxy: "http://localhost:4000/proxy"
	}
);
const styles = {
	fontFamily: "sans-serif",
	textAlign: "center"
};

const LoginFunc = () => {
	hello.login("linkedin").then(function() {
		hello("linkedin")
			.api("me")
			.then(function(p) {
				console.log(p)
			});
	});
};

const App = () => (
	<div style={styles}>
		<Hello name="CodeSandbox" />
		<h2>Start editing to see some magic happen {"\u2728"}</h2>
		<button id="login" onClick={LoginFunc}>
			LinkedIn
		</button>
	</div>
);


render(<App />, document.getElementById("root"));

hello.on("auth.login", function(r) {
	// Get Profile
	hello("linkedin")
		.api("me")
		.then(function(p) {
			console.log(p);
		});
});