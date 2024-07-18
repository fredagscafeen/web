/*jshint esversion: 11 */

function switchTheme() {
    "use strict";
    const isLightMode = document.documentElement.classList.contains("light");
    document.documentElement.classList.toggle("light", !isLightMode);
    document.documentElement.classList.toggle("dark", isLightMode);
    localStorage.setItem("lightMode", !isLightMode);
    localStorage.setItem("darkMode", isLightMode);
    if (isLightMode) {
        document.getElementById("facebook-link").setAttribute("class", "image-inverted social-link");
        document.getElementById("instagram-link").setAttribute("class", "image-inverted social-link");
        document.getElementById("github-link").setAttribute("class", "image-inverted social-link");
        try {
            document.getElementById("google-maps").setAttribute("style", "filter: invert(90%) hue-rotate(180deg); border: 0;");
        } catch(err) {
            // Page not selected
        }
    } else {
        document.getElementById("facebook-link").setAttribute("class", "social-link");
        document.getElementById("instagram-link").setAttribute("class", "social-link");
        document.getElementById("github-link").setAttribute("class", "social-link");
        try {
            document.getElementById("google-maps").setAttribute("style", "border: 0;");
        } catch(err) {
            // Page not selected
        }
    }
}

function setTheme() {
    "use strict";
    const prefersLightMode = window.matchMedia('(prefers-color-scheme: light)').matches;
    const isDarkMode = localStorage.getItem("darkMode") === "true" || (localStorage.getItem("darkMode") !== "false" && !prefersLightMode);

    document.documentElement.classList.toggle("dark", isDarkMode);
    document.documentElement.classList.toggle("light", !isDarkMode);
}

function setThemeToggle() {
    "use strict";
    const isDarkMode = document.documentElement.classList.contains("dark");
    if (isDarkMode) {
        document.getElementById("themeToggle").checked = true;
        document.getElementById("facebook-link").setAttribute("class", "image-inverted social-link");
        document.getElementById("instagram-link").setAttribute("class", "image-inverted social-link");
        document.getElementById("github-link").setAttribute("class", "image-inverted social-link");
        try {
            document.getElementById("google-maps").setAttribute("style", "filter: invert(90%) hue-rotate(180deg); border: 0;");
        } catch(err) {
            // Page not selected
        }
    }
}
