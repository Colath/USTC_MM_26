im_beach = imread('original.png'); 
added_width = 300;
new_size = size(im_beach, 1:2) + [0 added_width];

im_beach_scale = imresize(im_beach, new_size);

im_beach_sc = seam_carve_image(im_beach, new_size);
figure('Name', 'Beach Enlarge Compare', 'Units', 'pixel', 'Position', [100,100,1500,600]);
subplot(131); imshow(im_beach); title('Original Beach');
subplot(132); imshow(im_beach_sc); title('Seam Insertion (+300)');
subplot(133); imshow(im_beach_scale); title('Standard Scale (+300)');

function im = seam_carve_image(im, sz)
    original_class = class(im);
    im = double(im);
    costfunction = @(im) sum( imfilter(im, [.5 1 .5; 1 -6 1; .5 1 .5]).^2, 3 );

    [h, w, ~] = size(im);
    target_w = sz(2);
    k = abs(target_w - w);

    if target_w < w
        % lessen 
        for i = 1:k
            G = costfunction(im); [h, w] = size(G);
            M = zeros(h,w); M(1, :) = G(1, :);
            for r = 2:h
                m_left=[1e10, M(r-1,1:w-1)]; m_mid=M(r-1,:); m_right=[M(r-1,2:w),1e10];
                M(r, :) = G(r, :) + min([m_left; m_mid; m_right]);
            end
            seam = zeros(h, 1); [~, col] = min(M(h, :)); seam(h) = col;
            for r = h-1:-1:1
                prev_col = seam(r+1); 
                cols = max(1, prev_col-1) : min(w, prev_col+1);
                [~, idx] = min(M(r, cols)); seam(r) = cols(idx);
            end
            new_im = zeros(h, w-1, 3, class(im));
            for r = 1:h
                new_im(r, :, :) = im(r, [1:seam(r)-1, seam(r)+1:w], :);
            end
            im = new_im;
        end
    else
        % enlarge 
        fprintf('Enlarging image by %d pixels...\n', k);
       
        temp_im = im;
        Idx = repmat(1:w, h, 1); 
        all_seams = zeros(h, k); 
       
        for i = 1:k
            G = costfunction(temp_im); 
            [curr_h, curr_w] = size(G);
            M = zeros(curr_h, curr_w); M(1,:) = G(1,:);
            for r = 2:curr_h
                m_left=[1e10, M(r-1,1:curr_w-1)]; m_mid=M(r-1,:); m_right=[M(r-1,2:curr_w),1e10];
                M(r, :) = G(r, :) + min([m_left; m_mid; m_right]);
            end
            seam = zeros(curr_h, 1); 
            [~, col] = min(M(curr_h, :)); seam(curr_h) = col;
            for r = curr_h-1:-1:1
                prev_col = seam(r+1); 
                cols = max(1, prev_col-1) : min(curr_w, prev_col+1);
                [~, idx] = min(M(r, cols)); seam(r) = cols(idx);
            end
           
            new_temp_im = zeros(curr_h, curr_w-1, 3, class(temp_im));
            new_Idx = zeros(curr_h, curr_w-1);
            for r = 1:curr_h
                c = seam(r);
                all_seams(r, i) = Idx(r, c); 
                
                new_temp_im(r, :, :) = temp_im(r, [1:c-1, c+1:curr_w], :);
                new_Idx(r, :) = Idx(r, [1:c-1, c+1:curr_w]);
            end
            temp_im = new_temp_im;
            Idx = new_Idx;
        end
        
        new_w = w + k;
        new_im = zeros(h, new_w, 3, class(im));
        
        for r = 1:h
            cols_to_dup = all_seams(r, :); 
            new_idx = 1;
            
            for old_idx = 1:w
                new_im(r, new_idx, :) = im(r, old_idx, :);
                new_idx = new_idx + 1;
                
                if ismember(old_idx, cols_to_dup)
                    if old_idx < w
                        new_im(r, new_idx, :) = (im(r, old_idx, :) + im(r, old_idx+1, :)) / 2;
                    else
                        new_im(r, new_idx, :) = im(r, old_idx, :);
                    end
                    new_idx = new_idx + 1;
                end
            end
        end
        im = new_im;
    end

    if strcmp(original_class, 'uint8'), im = uint8(im); end
end
