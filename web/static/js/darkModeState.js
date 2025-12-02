/*jshint esversion: 11 */

function switchTheme() {
    "use strict";
    const isLightMode = document.documentElement.getAttribute('data-bs-theme') == 'light';
    localStorage.setItem("lightMode", !isLightMode);
    localStorage.setItem("darkMode", isLightMode);
    if (isLightMode) {
        document.documentElement.setAttribute('data-bs-theme','dark')

        try {
            document.getElementById("google-maps").setAttribute("style", "filter: invert(90%) hue-rotate(180deg); border: 0;");
        } catch(err) {
            // Page not selected
        }
        try {
            document.getElementById("timesheet-theme").classList = "black";
        } catch(err) {
            // Page not selected
        }
    } else {
        document.documentElement.setAttribute('data-bs-theme','light')

        try {
            document.getElementById("google-maps").setAttribute("style", "border: 0;");
        } catch(err) {
            // Page not selected
        }
        try {
            document.getElementById("timesheet-theme").classList = "white";
        } catch(err) {
            // Page not selected
        }
    }
}

function setTheme() {
    "use strict";
    const prefersLightMode = window.matchMedia('(prefers-color-scheme: light)').matches;
    const isDarkMode = localStorage.getItem("darkMode") === "true" || (localStorage.getItem("darkMode") !== "false" && !prefersLightMode);

    if (isDarkMode) {
        document.documentElement.setAttribute('data-bs-theme','dark')
    } else {
        document.documentElement.setAttribute('data-bs-theme','light')
    }
}

function setThemeToggle() {
    "use strict";
    const isDarkMode = document.documentElement.getAttribute('data-bs-theme') == 'dark';

    if (isDarkMode) {
        try {
            document.getElementById("themeToggle1").checked = true;
            document.getElementById("themeToggle2").checked = true;
        } catch(err) {
            // Page not selected
        }
        try {
            document.getElementById("google-maps").setAttribute("style", "filter: invert(90%) hue-rotate(180deg); border: 0;");
        } catch(err) {
            // Page not selected
        }
        try {
            document.getElementById("timesheet-theme").classList = "black";
        } catch(err) {
            // Page not selected
        }
    }
}
