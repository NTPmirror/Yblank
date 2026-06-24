const ymusic = {
    async doSomething(input) {
        if (window.go && window.go.ymusic && window.go.ymusic.App) {
            return await window.go.ymusic.App.DoSomething(input);
        }
        if (window.ymusicBridge) {
            return window.ymusicBridge.doSomething(input);
        }
        return "Platform not detected.";
    },

    async getVersion() {
        if (window.go && window.go.ymusic && window.go.ymusic.App) {
            return await window.go.ymusic.App.GetVersion();
        }
        if (window.ymusicBridge) {
            return window.ymusicBridge.getVersion();
        }
        return "0.0.0";
    }
};

window.addEventListener("DOMContentLoaded", async () => {
    const msg = document.getElementById("message");
    msg.textContent = `Version: ${await ymusic.getVersion()}`;
});
