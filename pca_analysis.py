from __future__ import division
import numpy as np
import matplotlib.pyplot as plt


def nextpow2(n):
    m_f = np.log2(n)
    m_i = np.ceil(m_f)
    return int(np.log2(2**m_i))

def pre_analysis(time, dt, period, plot_check=False):
	"""
	Given an initial frequncy, finds a better one using FFT
	"""

	freq_start = 1 / period

	# Setting the x axis for histogram, represents the time descrete position
	time_axis = np.arange(0, time[len(time) - 1], dt)
	# counts the number of values in time that are within each specified bin range, time_axis
	bin_data = np.histogram(time, bins=time_axis)[0]

	fs = 1 / dt # frequency step

	# Fast Fourier Transform computation
	NFFT = 2 ** nextpow2(len(bin_data)) # Length of the transformed axis of the output
	y = np.fft.fft(bin_data, NFFT) # Computed FFT
	N = NFFT / 2 + 1 # indices to erase the mirror effect from FFT
	Y = np.abs(y[:N]) # cleaned from all mirror effects
	freq_axis = fs / 2 * np.linspace(0, 1, N)

	# To give a zero value to the first components, due to FFT
	k = 100;
	for i in np.arange(0, k, 1):
		Y[i] = 0

	start = int(len(freq_axis) * freq_start * 2 / fs) - 1
	stop = int(len(freq_axis) * freq_start * 2 / fs * 2)
	Y_selected = Y[np.arange(start, stop, dtype=int)]

	# Selection of the index in the freq_axis array
	index = np.argmax(Y_selected)

	frequency = freq_axis[index + int(len(freq_axis) * freq_start * 2 / fs)]

	if plot_check:

		fig1, ax1 = plt.subplots()
		ax1.hist(bin_data, histtype='stepfilled') 
		ax1.set_title('Histogram dt = ' + str(dt))
		ax1.set_ylabel('Photon counts')
		ax1.set_xlabel('Time in ' + str(dt) + ' s units')
		ax1.grid()

		fig2, ax2 = plt.subplots()
		ax2.plot(freq_axis, Y)
		ax2.set_title('FFT binned data')
		ax2.set_ylabel('Amplitude')
		ax2.set_xlabel('Frequency Hz')
		ax2.grid()

		plt.show()

	return bin_data, frequency

def new_fold(time, dt, period, num_div, plot_check=False):
	""" 
	Folding algorithm
	data is the .mat file which is a time array. It is a column vector
	num_div is the number of divisions made to the time array (aka data) or rows in waterfall
	The period will only be an approximation, needs to be iterated to correct it!
	"""
	if period < dt:
		print('WARNING: Period cannot be smaller than bin size (dt)')

	# Length light-curve
	# N represents the columns in the waterfall
	Nint = round(period / dt) # It has to be chosen the int value over the approximation.
	dt = period / Nint # dt recalculated so it becomes an interger for given period
	
	print('Nint = ' + str(Nint))

	# Period division in Nint*dt. Bin array
	# arange isn't used, it ins't precise! 
	# period_div_dt = np.arange(0, period + dt, dt) # Difference with matlab 0:dt:period;
	period_div_dt = np.linspace(0, period, Nint, endpoint=True) # Recheck this point!

	# number of samples that will be considered for each row of the waterfall
	num_samples = np.floor(len(time) / num_div)

	# Modulus divions or what is left. Return element-wise remainder of division.
	remainder = np.mod(time, period)

	# for each line in the waterfall diagram
	for line in np.arange(0, num_div, dtype=int):
		# selection of each num_div in time array
		indices = np.arange(num_samples * line, num_samples * (line + 1), dtype=int) 
		# matrix that contains info for waterfall diagram
		if line == 0:
			waterfall = np.histogram(remainder[indices], bins=period_div_dt)[0]
		else:
			waterfall = np.vstack((waterfall, np.histogram(remainder[indices], bins=period_div_dt)[0]))

	# Light-Curve plot
	lc = np.histogram(remainder, period_div_dt)[0]
	period_time_one = np.arange(0, period, dt)
	# Stacking two periods together for visualization 
	lc2 = np.hstack((lc, lc))
	period_time_two = np.arange(0, 2 * period, dt)

	if plot_check:
		fig1, ax1 = plt.subplots()
		ax1.plot(period_time_two, lc2, 'ro-', label='Period ' + str(period) + ' s', linewidth=1.5)
		ax1.set_title('Light curve dt = ' + str(dt) + ' s')
		ax1.set_xlabel('Time s')
		ax1.set_ylabel('Total counts')
		ax1.legend(loc='best')
		ax1.grid()

		fig2, ax2 = plt.subplots()
		im2 = ax2.imshow(waterfall, cmap=plt.cm.jet, interpolation='nearest', aspect='auto')
		cb = fig2.colorbar(im2, ax=ax2)
		cb.set_label('Total counts')
		ax2.set_title('Waterfall rows: ' + str(num_div) + ', dt = ' + str(dt) + ' s')
		ax2.set_xlabel('Bin s')
		ax2.set_ylabel('Light curves')
		ax2.grid()

		plt.show()

	return lc, waterfall

def fast_pca(waterfall, plot_check=False): 
	"""
	Finds PCs, eigenvalues and signal matrix.
	waterfall is a MxN matrix. Corresponds to the Waterfall diagram!
	M: rows, # segments in which the whole adquisition has been divided
	N: columns, # bins in folding period. Number of eigenvalues
	norm is the (waterfall - <waterfall>)/var(waterfall)
	V: eigenvalues cov
	PC: eigenvector cov. The column PC[:,i] is the eigenvector
	"""
	M, N = waterfall.shape # This should be the waterfall matrix
	mean = np.mean(waterfall, axis=1).reshape(M, 1)
	std = np.std(waterfall, axis=1, ddof=1).reshape(M, 1) # carful, different in matlab!

	# normalization waterfall matrix to mean=0 and std=1
	norm = (waterfall - mean) / std
	# Covariance matrix
	#cov = np.cov(norm.T)
	cov = 1 / (N - 1) * np.dot(norm,norm.T)

	# Eigenvalue, Eigenvector
	V, PC = np.linalg.eig(cov)

	print('Eigenvalues = ' + str(V))

	V_sorted = np.sort(V.real)[::-1] # Eigenvalue
	j_indices = np.argsort(V.real)[::-1]
	PC_sorted = PC[:, j_indices] # Eigenvector or PCs

	signals = np.dot(PC_sorted.T, norm) # Information matrix, not clear

	# Plot to visualize the PCs
	if plot_check:
		width = 0.8
		ind = np.arange(0, len(V_sorted))

		fig1, ax1 = plt.subplots()
		ax1.bar(ind, V_sorted, width=width)
		ax1.set_xlabel('Component value')
		ax1.set_ylabel('Eigenvalue')
		ax1.set_title('PCA values')
		ax1.set_xticks(ind + width/2)
		ax1.set_xticklabels(np.arange(1, len(V) + 1, dtype=int))
		ax1.grid()
		ax1.set_ylim([-0.1, V_sorted[0] + 0.1])
		ax1.set_xlim([-0.1, len(V)])

		fig2, ax2 = plt.subplots()
		im2 = ax2.imshow(signals, interpolation='nearest', aspect='auto')
		cb2 = fig2.colorbar(im2, ax=ax2)
		cb2.set_label('Norm(0, 1) counts')
		ax2.set_title(r"$\mathrm{Signal} \, = \, \mathrm{PC}^T\times\,\,\frac{W-\bar{W}}{\sigma(W)}$")
		ax2.set_xlabel('Bins s')
		ax2.set_ylabel('Light curves')
		ax2.grid()

		fig3, ax3 = plt.subplots()
		im3 = ax3.imshow(norm, interpolation='nearest', aspect='auto')
		cb3 = fig3.colorbar(im3, ax=ax3)
		cb3.set_label('Norm(0, 1) counts')
		ax3.set_title(r"$\mathrm{Normalization} \,=\, \frac{W-\bar{W}}{\sigma(W)}$")
		ax3.set_xlabel('Bins s')
		ax3.set_ylabel('Light curves')
		ax3.grid()

		plt.show()

	return V_sorted.tolist(), PC_sorted.tolist(), cov, norm, signals

def delta_finder(period, iterations, delta, time, dt, num_div):

	# makes an interval from central period, [period - i/2 * delta, period + i/2 * delta]
	period_iter = period - iterations / 2 * delta
	variance = []
	
	eigenvalues_all = []
	eigenvectors_all = []

	for i in range(0, iterations):
		waterfall = new_fold(time, dt, period_iter, num_div)[1]
		eigenvalues, eigenvectors, _, _, _ = fast_pca(waterfall)

		print('Eigen values shape = ' + str(np.array(eigenvalues).shape))

		# Stores only the first PC for method1
		variance.append(eigenvalues[0])

		# Store all PC and V for other purposes
		eigenvalues_all.append(eigenvalues)
		eigenvectors_all.append(eigenvectors)

		period_iter += delta
	
	# Optimum selection, which will correspond to the maximum
	max_index = np.argmax(variance)
	period_final = period + (max_index - iterations / 2) * delta

	return period_final, variance, eigenvalues_all, eigenvectors_all

def find_period(time, period, dt, num_div, iter1, delta1, iter2, delta2, noisy_signal=False):
	"""
	Finds the optimal period using PCA. 
	"""
	freq = 1 / period

	if noisy_signal:
		freq_start = freq
	else:
		freq_start = pre_analysis(time, dt, period)[1]

	# Separation for one or two iterations
	if iter2 != 0:
		period_start1 = 1 / freq_start
		period_final1, variance1, eigenvalues_all1, eigenvectors_all1 = delta_finder(period_start1, \
			iter1, delta1, time, dt, num_div)

		period_start2 = period_final1
		period_final2, variance2, eigenvalues_all2, eigenvectors_all2 = delta_finder(period_start2, \
			iter2, delta2, time, dt, num_div)

	else:
		period_start1 = 1 / freq_start
		period_final1, variance1, eigenvalues_all1, eigenvectors_all1 = delta_finder(period_start1, \
			iter1, delta1, time, dt, num_div)

		period_final2 = 0
		variance2 = 0
		eigenvalues_all2 = 0
		eigenvectors_all2 = 0


	return np.array([1/freq, period_start1, period_final1, period_final2]), np.array([variance1, variance2]), \
	[eigenvalues_all1, eigenvalues_all2], [eigenvectors_all1, eigenvectors_all2]







# import scipy.io as sio
# path = '/Users/tomascassanelli/Dropbox/PCA.A&A/Verroi/MATLAB/'
# file_name = 'rmr0'
# matlab_file = sio.loadmat(path + file_name + '.mat')
# time = matlab_file['time']
# dt = 0.004
# period = 0.089367
# num_div = 20

# Per, Var, _, _ = find_period(time, period, dt, num_div, 100, 1e-7, 1000, 1e-9, noisy_signal=True)
# print(Per)
# plt.plot(Var[1])
# plt.grid
# plt.show()
	
