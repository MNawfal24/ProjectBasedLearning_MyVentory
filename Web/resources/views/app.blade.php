<!DOCTYPE html>
<html lang="id" class="h-full">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title inertia>{{ config('app.name') }}</title>
    <link rel="icon" type="image/png" href="/logo.png">
    <link rel="apple-touch-icon" href="/logo.png">
    <script>
        // Applied before first paint so the stored theme never flashes the wrong surface.
        (function () {
            var stored = localStorage.getItem('myventory-theme');
            var dark = stored ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.classList.toggle('dark', dark);
        })();
    </script>
    @vite(['resources/css/app.css', 'resources/js/app.js'])
    @inertiaHead
</head>
<body class="min-h-full bg-canvas text-ink antialiased">
    @inertia
</body>
</html>
