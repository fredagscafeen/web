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
        try {
            document.getElementById("timesheet-theme").classList = "black";
        } catch(err) {
            // Page not selected
        }
        const panels = document.getElementsByClassName("panel");
        for (let i = 0; i < panels.length; i++) {
            panels[i].classList = "panel panel-primary";
        }
        const success = document.getElementsByClassName("success");
        for (let n = 0; n < 5; n++) {
            for (let i = 0; i < success.length; i++) {
                success[i].classList = "success-dark";
            }
        }
        const danger = document.getElementsByClassName("danger");
        for (let n = 0; n < 5; n++) {
            const danger = document.getElementsByClassName("danger");
            for (let i = 0; i < danger.length; i++) {
                danger[i].classList = "danger-dark";
            }
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
        try {
            document.getElementById("timesheet-theme").classList = "white";
        } catch(err) {
            // Page not selected
        }
        const panels = document.getElementsByClassName("panel");
        for (let i = 0; i < panels.length; i++) {
            panels[i].classList = "panel panel-default";
        }
        const success = document.getElementsByClassName("success-dark");
        for (let i = 0; i < success.length; i++) {
            success[i].classList = "success";
        }
        const danger = document.getElementsByClassName("danger-dark");
        for (let i = 0; i < danger.length; i++) {
            danger[i].classList = "danger";
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
        document.getElementById("themeToggleNav").checked = true;
        document.getElementById("facebook-link").setAttribute("class", "image-inverted social-link");
        document.getElementById("instagram-link").setAttribute("class", "image-inverted social-link");
        document.getElementById("github-link").setAttribute("class", "image-inverted social-link");
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
        const panels = document.getElementsByClassName("panel");
        for (let i = 0; i < panels.length; i++) {
            panels[i].classList = "panel panel-primary";
        }
        const success = document.getElementsByClassName("success");
        for (let i = 0; i < success.length; i++) {
            success[i].classList = "success-dark";
        }
        for (let n = 0; n < 5; n++) {
            const danger = document.getElementsByClassName("danger");
            for (let i = 0; i < danger.length; i++) {
                danger[i].classList = "danger-dark";
            }
        }
    }
}
