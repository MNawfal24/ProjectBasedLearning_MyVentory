<!DOCTYPE html>
<html lang="id" class="h-full">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ $title }} · MyVentory</title>
    <script>
        (function () {
            var stored = localStorage.getItem('myventory-theme');
            var dark = stored ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
            document.documentElement.classList.toggle('dark', dark);
        })();
    </script>
    @vite(['resources/css/app.css'])
</head>
<body class="min-h-full bg-canvas text-ink antialiased">
    <main class="mx-auto flex min-h-screen w-full max-w-lg flex-col justify-center px-6 py-16">
        <p class="numeric text-sm font-medium text-primary">{{ $code }}</p>
        <h1 class="mt-2 text-2xl font-semibold tracking-tight">{{ $title }}</h1>
        <p class="mt-2 text-sm leading-relaxed text-muted">{{ $message }}</p>
        <div class="mt-6">
            <a href="/" class="btn">Kembali ke overview</a>
        </div>
    </main>
</body>
</html>
