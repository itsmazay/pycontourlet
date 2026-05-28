function val = get(h, prop)
    % Headless stub for Octave's get() -- only used inside showpdfb.m to
    % query the figure colormap and background color. We don't have a
    % graphics context, so return canned values that match what MATLAB's
    % default figure provides.
    switch lower(prop)
        case 'colormap'
            % MATLAB's default: 256-entry gray colormap.
            val = repmat(linspace(0, 1, 256)', 1, 3);
        case 'color'
            % MATLAB's default figure background.
            val = [0.94, 0.94, 0.94];
        otherwise
            val = [];
    end
end
