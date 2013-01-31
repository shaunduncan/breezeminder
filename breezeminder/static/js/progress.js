(function($, global) {

    global.ProgressDialog = function(numSteps, show) {
        this.numSteps = numSteps;
        this.stepNum = 1;
        this.el = this._create();

        if(show) {
            this.show();
        }
    }

    ProgressDialog.fn = ProgressDialog.prototype;

    /*
     * Creates the dialog in the DOM
     */
    ProgressDialog.fn._create = function() {
        var id = 'progress' + (new Date()).getTime();

        // Create the modal target
        $('body').append('<div id="' + id + '" class="modal hide">'
            + '<div class="modal-header"><h3>Loading...</h3></div>'
            + '<div class="modal-body"><p>Please Wait</p>'
            + '<div class="progress progress-striped active">'
            + '<div class="bar" style="width: 0%"></div></div>'
            + '</div></div>');

        return $('#' + id);
    }

    /*
     * Shows the dialog
     */
    ProgressDialog.fn.show = function() {
        this.el.modal({keyboard: false});
    }

    /*
     * Step the progress dialog with a message.
     * Returns the current step number
     */
    ProgressDialog.fn.step = function(info, num) {
        // Check false-y
        if(num || num == 0) this.stepNum = num;
        var progress = Math.min((100.0/this.numSteps) * ++this.stepNum);

        this.el.find('p').html(info);
        this.el.find('.bar').css('width', progress + '%');

        return this.stepNum;
    }

    /*
     * Advances the current step number and returns it
     */
    ProgressDialog.fn.advance = function() {
        return this.stepNum++;
    }

    /*
     * Decrements the step counter by 1 and returns it
     */
    ProgressDialog.fn.back = function() {
        return this.stepNum--;
    }

    /*
     * Completes the progress at 100% and destroys after a timeout
     */
    ProgressDialog.fn.complete = function() {
        this.el.find('p').html('Complete!');
        this.el.find('.bar').css('width', '100%');

        setTimeout($.proxy(this.destroy, this), 500);
    }

    /*
     * Removes the dialog from the DOM
     */
    ProgressDialog.fn.destroy = function() {
        this.el.modal('hide');
        this.el.remove();
    }

})(jQuery, this);
