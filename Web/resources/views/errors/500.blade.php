@include('errors.layout', [
    'code' => '500',
    'title' => 'Terjadi kesalahan',
    'message' => 'Permintaan ini gagal diproses. Coba lagi sebentar lagi; kalau tetap gagal, periksa log container web.',
])
