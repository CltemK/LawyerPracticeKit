package com.phoneguardian.ui.settings

import android.app.TimePickerDialog
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.phoneguardian.databinding.FragmentSettingsBinding
import kotlinx.coroutines.launch

class SettingsFragment : Fragment() {

    private var _binding: FragmentSettingsBinding? = null
    private val binding get() = _binding!!

    private val viewModel: SettingsViewModel by viewModels()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentSettingsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupClickListeners()
        observeUiState()
    }

    private fun setupClickListeners() {
        binding.cardSleepTime.setOnClickListener {
            showSleepStartTimePicker()
        }

        binding.cardSleepEndTime.setOnClickListener {
            showSleepEndTimePicker()
        }

        binding.cardDataRetention.setOnClickListener {
            showRetentionDaysPicker()
        }

        binding.cardUsagePermission.setOnClickListener {
            openUsageAccessSettings()
        }

        binding.switchNotification.setOnCheckedChangeListener { _, isChecked ->
            viewModel.setNotificationEnabled(isChecked)
        }
    }

    private fun observeUiState() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.uiState.collect { state ->
                    binding.tvSleepStartValue.text = state.sleepStartTime
                    binding.tvSleepEndValue.text = state.sleepEndTime
                    binding.tvRetentionDaysValue.text = "${state.dataRetentionDays} 天"
                    binding.switchNotification.isChecked = state.notificationEnabled
                }
            }
        }
    }

    private fun showSleepStartTimePicker() {
        val current = viewModel.uiState.value.sleepStartTime
        val parts = current.split(":")
        val hour = parts[0].toInt()
        val minute = parts[1].toInt()

        TimePickerDialog(requireContext(), { _, h, m ->
            val time = String.format("%02d:%02d", h, m)
            viewModel.setSleepStartTime(time)
        }, hour, minute, true).show()
    }

    private fun showSleepEndTimePicker() {
        val current = viewModel.uiState.value.sleepEndTime
        val parts = current.split(":")
        val hour = parts[0].toInt()
        val minute = parts[1].toInt()

        TimePickerDialog(requireContext(), { _, h, m ->
            val time = String.format("%02d:%02d", h, m)
            viewModel.setSleepEndTime(time)
        }, hour, minute, true).show()
    }

    private fun showRetentionDaysPicker() {
        val options = arrayOf("30 天", "60 天", "90 天", "180 天")
        val values = intArrayOf(30, 60, 90, 180)
        val currentValue = viewModel.uiState.value.dataRetentionDays
        val currentIndex = values.indexOf(currentValue).coerceAtLeast(0)

        androidx.appcompat.app.AlertDialog.Builder(requireContext())
            .setTitle("数据保留天数")
            .setSingleChoiceItems(options, currentIndex) { dialog, which ->
                viewModel.setDataRetentionDays(values[which])
                dialog.dismiss()
            }
            .show()
    }

    private fun openUsageAccessSettings() {
        val intent = Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)
        startActivity(intent)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
