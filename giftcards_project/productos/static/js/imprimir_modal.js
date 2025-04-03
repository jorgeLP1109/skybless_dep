(function($) {
    $(document).ready(function() {
        $('.imprimir-link').click(function(e) {
            e.preventDefault();
            var codigoId = $(this).data('codigo-id');

            // Obtener el contenido del recibo mediante AJAX
            $.ajax({
                url: '/productos/recibo/' + codigoId + '/',  // Reemplaza con la URL de tu vista de recibo
                success: function(data) {
                    $('#modal-recibo').dialog({
                        modal: true,
                        width: 400,  // Ancho fijo de 400 píxeles
                        // O
                        maxWidth: 600,  // Ancho máximo de 600 píxeles
                        title: 'Recibo de Compra'
                    });
                }
            });
        });
    });
})(django.jQuery);