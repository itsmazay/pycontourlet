function map = colormap(varargin)
    % Headless stub for Octave's colormap() -- returns a 256-entry gray
    % colormap so showpdfb's `cColorInx = size(cmap, 1)` resolves to 256.
    map = repmat(linspace(0, 1, 256)', 1, 3);
end
